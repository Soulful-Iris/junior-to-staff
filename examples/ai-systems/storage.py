"""Persistence adapters: identical optimistic concurrency contract, local and AWS."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import sqlite3


class Conflict(Exception):
    """The caller must reload state; never blindly overwrite another writer."""


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def sync_directory(path):
    """POSIX durability boundary; fail explicitly on unsupported filesystems."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class LocalStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "state.sqlite", timeout=5)
        self.db.execute("CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, revision INTEGER, payload TEXT)")
        self.db.commit()

    def get(self, key):
        row = self.db.execute("SELECT revision,payload FROM state WHERE key=?", (key,)).fetchone()
        return (row[0], json.loads(row[1])) if row else (0, None)

    def put(self, key, value, revision):
        with self.db:
            if revision == 0:
                try:
                    self.db.execute("INSERT INTO state VALUES (?,?,?)", (key, 1, encode(value)))
                except sqlite3.IntegrityError as exc:
                    raise Conflict(key) from exc
            else:
                updated = self.db.execute("UPDATE state SET revision=?,payload=? WHERE key=? AND revision=?",
                                          (revision + 1, encode(value), key, revision))
                if updated.rowcount != 1:
                    raise Conflict(key)
        return revision + 1

    def write_object(self, value):
        data = encode(value).encode("utf-8")
        key = hashlib.sha256(data).hexdigest() + ".json"
        destination = self.directory / key
        if destination.exists():
            if destination.read_bytes() != data:
                raise ValueError("content-addressed object is corrupt")
            sync_directory(self.directory)
            return key  # Never reopen an already published object for writing.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory, prefix=".object-", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            # Same-filesystem, no-clobber publication: readers see all bytes or none.
            try:
                os.link(temporary, destination)
            except FileExistsError:
                if destination.read_bytes() != data:
                    raise ValueError("content-addressed object is corrupt")
            sync_directory(self.directory)
            return key
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def read_object(self, key):
        if Path(key).name != key:
            raise ValueError("invalid object key")
        return json.loads((self.directory / key).read_text())


class AwsStore:
    def __init__(self, table_name, bucket, tenant):
        import boto3
        self.table = boto3.resource("dynamodb").Table(table_name)
        self.s3 = boto3.client("s3")
        self.bucket, self.prefix = bucket, tenant + "/"

    def get(self, key):
        item = self.table.get_item(Key={"pk": key}, ConsistentRead=True).get("Item")
        return (int(item["revision"]), json.loads(item["payload"])) if item else (0, None)

    def put(self, key, value, revision):
        from botocore.exceptions import ClientError
        request = {"Item": {"pk": key, "revision": revision + 1, "payload": encode(value)},
                   "ConditionExpression": "attribute_not_exists(pk)" if revision == 0 else "revision = :expected"}
        if revision:
            request["ExpressionAttributeValues"] = {":expected": revision}
        try:
            self.table.put_item(**request)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise Conflict(key) from exc
            raise
        return revision + 1

    def write_object(self, value):
        key = self.prefix + fingerprint(value) + ".json"
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=encode(value).encode(), ContentType="application/json")
        return key

    def read_object(self, key):
        if not key.startswith(self.prefix):
            raise ValueError("object belongs to another tenant")
        return json.loads(self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read())
