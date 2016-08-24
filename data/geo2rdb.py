import argparse
import os
import json
import glob
import re
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from config import config, refLookup

ref_regex = re.compile(r'<a href=.+?>(.+?:.+?)<')
NEWDB = 'bgeo'
LOCTABLE = 'locations'
REFTABLE = 'references'
def get_db_conn():
    try:
        connection = r.connect(config['rdb']['host'], config['rdb']['port'])
    except RqlRuntimeError, e:
        print 'App database already exists. Run the app without --setup.'
        print e
        connection = False
    finally:
        return connection

def pop_bible_lookup(c):
    bookChaps = {
            'Genesis': 50,
            'Exodus': 40,
            'Leviticus': 27,
            'Numbers': 36,
            'Dueteronomy': 34,
            'Joshua': 24,
            'Judges': 21,
            'Ruth': 4,
            'I Samuel': 31,
            'II Samuel': 24,
            'I Kings': 22,
            'II Kings': 25,
            'I Chronicles': 29,
            'II Chronicles': 36,
            'Ezra': 10,
            'Nehemiah': 13,
            'Esther': 10,
            'Job': 42,
            'Psalms': 150,
            'Proverbs': 31,
            'Ecclesiastes': 12,
            'The Song of Songs': 8,
            'Isaiah': 66,
            'Jeremiah': 52,
            'Lamentations': 5,
            'Ezekiel': 48,
            'Daniel': 12,
            'Hosea': 14,
            'Joel': 3,
            'Amos': 9,
            'Obadiah': 1,
            'Jonah': 4,
            'Micah': 7,
            'Nahum': 3,
            'Habakkuk': 3,
            'Zephaniah': 3,
            'Haggai': 2,
            'Zechariah': 14,
            'Malachi': 4,
            'Matthew': 28,
            'Mark': 16,
            'Luke': 24,
            'John': 21,
            'Acts': 28,
            'Romans': 16,
            'I Corinthians': 16,
            'II Corinthians': 13,
            'Galatians': 6,
            'Ephesians': 6,
            'Philippians': 4,
            'Colossians': 4,
            'I Thessalonians': 5,
            'II Thessalonians': 3,
            'I Timothy': 6,
            'II Timothy': 3,
            'Titus': 3,
            'Philemon': 1,
            'Hebrews': 13,
            'James': 5,
            'I Peter': 5,
            'II Peter': 3,
            'I John': 5,
            'II John': 1,
            'III John': 1,
            'Jude': 1,
            'Revelation': 22
        }
    for k, v in bookChaps.iteritems():
        r.db(NEWDB).table('books').insert(rec).run(c)



def get_location_id(conn, locName):
    res = list(r.db(NEWDB).table(LOCTABLE).filter({'name':locName}).run(conn))
    locID = False
    if len(res) == 1:
        locID = res[0]['id']
    return  locID

def parse_geojson_locations(conn, jsonfile):
    with open(jsonfile) as f:
        data = json.loads(f.read())
        for feat in data['features']:
            locRec = {}
            props = feat['properties']
            locRec['name'] = props['Name']
            if locRec['name'][-1] in ['~', '>', '<']:
                locRec['name'] = locRec['name'][:-1]
            locRec['location'] = feat['geometry']
            locID = insert_location(conn, LOCTABLE, locRec)


def parse_geojson_references(conn, jsonfile):
    with open(jsonfile) as f:
        data = json.loads(f.read())
        for feat in data['features']:
            locRec = {}
            props = feat['properties']
            locRec['name'] = props['Name']
            if locRec['name'][-1] in ['~', '>', '<']:
                locRec['name'] = locRec['name'][:-1]
            locRec['location'] = feat['geometry']
            # Get and delete description field before insertion
            #desc = feat['properties'].pop('Description', None)
            locid = insert_location(conn, LOCTABLE, locRec)
            if locid:
                findRefs = ref_regex.findall(props['Description'])
                #print(findRef.group(1))
                for findRef in findRefs:
                    d = {}
                    d['name'] = locRec['name']
                    d['ref'] = findRef
                    #print(d['ref'])
                    #print('Can you see me?')
                    tRef = d['ref'].split(' ')
                    if len(tRef) == 2:
                        rBook = tRef[0]
                        rCh, rVer = tRef[1].split(':')
                    elif len(tRef) == 3:
                        rBook = tRef[0] + ' ' + tRef[1]
                        rCh, rVer = tRef[2].split(':')
                    d['book'] = [k for k,v in refLookup.iteritems() if rBook in v][0].lower()
                    d['chapter'] = rCh
                    d['verse'] = rVer
                    refAsIndex = [d['book'], d['chapter'], d['verse']]
                    curRef = get_reference_by_brefIndex(conn, REFTABLE, refAsIndex)
                    if curRef:
                        newRef = curRef['loc_ref'].append(locid)
                        replace_ref_loc(conn, REFTABLE, curRef['id'], newRef)
                    else:
                        d['loc_ref'] = [locid]
                        insert_reference(conn, REFTABLE, d)
            else:
                print('A new location: {0}'.format(d['name']))


def get_reference_by_brefIndex(connection, dstTable, bi):
    res = list(r.db(NEWDB).table(dstTable).get_all(bi, index='brefIndex').run(connection))
    if len(res) == 1:
        print res[0]
        return res[0]
    elif len(res) > 1:
        print('Returned multiple results for a bref lookup... not good?!')
        len(res)
        print(bi)
        return False
    else:
        return False

def insert_location(connection, dstTable, rec):
    res = r.db(NEWDB).table(dstTable).insert({
        'name': rec['name'],
        'location': r.geojson(rec['location'])},
        return_changes=True
    ).run(connection)
    return res['changes'][0]['new_val']['id']

def replace_ref_loc(connection, dstTable, recID, newRef):
    print(newRef)
    r.db(NEWDB).table(dstTable).get(recID).replace({'loc_ref': newRef}).run(connection)

def insert_reference(connection, dstTable, rec):
    r.db(NEWDB).table(dstTable).insert({
        'name': rec['name'],
        'bref': rec['ref'],
        'book': rec['book'],
        'chapter': rec['chapter'],
        'verse': rec['verse'],
        'loc_ref': rec['loc_ref']
    }).run(connection)


def populate_new_db(conn, sPath=None):
    if sPath is None:
        sPath = './'
    r.db(NEWDB).table(LOCTABLE).index_create("name").run(conn)
    parse_geojson_references(conn, sPath + 'all.json')
    #pathName = sPath + '*.json'
    #files = glob.glob(pathName)
    #for f in files:
    #    if f.endswith('all.json'):
    #        continue
    #    else:
    #        parse_geojson_references(conn, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the bgeo app.')
    parser.add_argument('--setup', dest='run_setup', action='store_true')
    parser.add_argument('--source', dest='source', action='store')

    args = parser.parse_args()
    if args.run_setup:
        c = get_db_conn()
        if c:
            r.db_create(NEWDB).run(c)
            r.db(NEWDB).table_create(LOCTABLE).run(c)
            r.db(NEWDB).table_create(REFTABLE).run(c)
            r.db(NEWDB).table(REFTABLE).index_create("loc_ref", multi=True).run(c)
            r.db(NEWDB).table(REFTABLE).index_create("brefIndex", [
                r.row['book'], 
                r.row['chapter'], 
                r.row['verse']
            ]).run(c)
            r.db(NEWDB).table(REFTABLE).index_wait("brefIndex").run(c)
            populate_new_db(c, args.source)
        else:
            print "nothing here yet."




