import subprocess, json, os, shutil, pytz
commits = set(subprocess.check_output(['git', 'rev-list', '--all']).split())

nameroot = 'wordcount'
txtname= nameroot + '.txt'
dbname = nameroot + '.json'
tmpdir = os.path.join(os.environ['TMPDIR'], nameroot)
try:
  dbfile = open(dbname, 'r')
  dbdict = json.load(dbfile)
  dbfile.close()
except IOError:
  print "Couldn't open %s, starting with a clean dictionary"%(dbname)
  dbdict = { }

knowncommits = set(dbdict.keys())
newcommits = commits - knowncommits

for commit in newcommits:
  date = subprocess.check_output(['git', 'log', '-n', '1', '--pretty=%ad',
    commit]).strip()
  if os.path.exists(tmpdir):
    shutil.rmtree(tmpdir)
  os.mkdir(tmpdir)

  gitcmd = subprocess.Popen(['git', 'archive', commit], stdout=subprocess.PIPE)
  tarcmd = subprocess.Popen(['tar', '-x', '-C', tmpdir], stdin=gitcmd.stdout,
      stdout=subprocess.PIPE)
  gitcmd.stdout.close()
  tarcmd.communicate()[0]

  def makeandcount(filename):
    makecmd = subprocess.Popen(['make', filename], cwd = tmpdir)
    makecmd.wait()
    if makecmd.returncode == 0:
      totext = subprocess.Popen(['pdftotext', filename, '-'],
          stdout = subprocess.PIPE, cwd = tmpdir)
      remnum = subprocess.Popen(['egrep', '-o', '[a-zA-Z]+'],
          stdout = subprocess.PIPE, stdin = totext.stdout, cwd = tmpdir)
      remlet = subprocess.Popen(['egrep', '-e', r'\w\w+'],
          stdout = subprocess.PIPE, stdin = remnum.stdout, cwd = tmpdir)
      counter= subprocess.Popen(['wc', '-w'], stdin = remlet.stdout,
          stdout = subprocess.PIPE, cwd = tmpdir)
      totext.stdout.close()
      count = counter.communicate()[0].strip()
      try:
        count = int(count)
        return count
      except:
        raise
    return None

  for name in ['thesis.pdf', 'main.pdf']:
    wordcount = makeandcount(name)
    if wordcount is not None:
      break

  dbdict[commit] = {
      'date' : date,
      'wordcount' : wordcount
      }

# Write the database
dbfile = open(dbname, 'w')
json.dump(dbdict, dbfile)
dbfile.close()

# Sort the info for output
from dateutil import parser
sortlist = [ ]

for commit, info in dbdict.iteritems():
  # The git log messages contain timezone information, convert everything to UTC
  dt = parser.parse(info['date']).astimezone(pytz.utc)
  wc = info['wordcount']
  if wc is not None:
    sortlist.append((dt, wc))

sortlist.sort()

# Define the text format for dates in the output file.
def fmt(date):
  return date.strftime('%Y.%m.%d %H:%M:%S')

txtfile = open(txtname, 'w')
txtfile.write('### %s ###\n'%(txtname))
lastwc = None
for date, wc in sortlist:
  tformat = fmt(date)
  if wc != lastwc:
    txtfile.write("%s %d\n"%(tformat, wc))
  lastwc = wc
txtfile.close()

# You might want to copy your results to a remote server, e.g.
#subprocess.Popen(['scp', txtname, 'example.com:wordcount_olli.txt'])
