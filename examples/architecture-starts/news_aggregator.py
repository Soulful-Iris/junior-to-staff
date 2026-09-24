"""Local mechanism demonstration for news-aggregator. No AWS resources are created."""
articles={}; etag='v1'
def ingest(source,item,url,title):
    key=(source,item); articles[key]={'url':url,'title':title}
    return 'upserted '+str(key)
print(ingest('publisher-a','42','https://example.invalid/story','First title'))
print(ingest('publisher-a','42','https://example.invalid/story','Corrected title'))
print('304 response: retain existing articles',articles)
