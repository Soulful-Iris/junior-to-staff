"""Local mechanism demonstration for a-public-form. No AWS resources are created."""
import csv,io
rows=[['Ana','00123','=1+1\nPlease call after six']]
def spreadsheet_text(value):
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value
out=io.StringIO(newline=''); writer=csv.writer(out)
writer.writerow(['name','phone','notes'])
for row in rows: writer.writerow([row[0],"'"+row[1],spreadsheet_text(row[2])])
print(out.getvalue()); print('Stored originals:',rows)
