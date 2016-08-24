import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from flask import Flask, jsonify, request, render_template, redirect, abort
from flask_cors import CORS, cross_origin
import requests

from config import config, refSort, refLookup
import json, sys
app = Flask(__name__)
app.debug=True
CORS(app)
placeFilters = []

def getBookId(book):
    try:
        return refSort[book]
    except KeyError:
        return 999

def sortRefs(refs):
    sortedRefs = sorted(refs, key=lambda x: (refSort[x['book']], x['chapter'], x['verse']))
    xRefs = []
    for r in sortedRefs:
        shortName = refLookup[r['book']][0]
        xRefs.append("{0} {1}:{2}".format(shortName.title(), r['chapter'], r['verse']))
    return xRefs

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/about.html', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/proxy/api/v1.0/bible-api/<bref>', methods=['GET'])
def proxy_bapi_search(bref):
    translation = request.args.get('translation')
    print('Translation param: {0}'.format(translation))
    qurl = 'http://bible-api.com/{0}?translation=kjv'.format(bref)
    print(qurl)
    res = requests.get(qurl).text
    print(res)
    return res
    #return jsonify(requests.get('http://bible-api.com/{0}'.format(query)).text)

@app.route('/bgeo/api/v1.0/be/location/search', methods=['GET'])
def get_be_location_search():
    search = request.args.get('query')
    res = {}
    if search:
        c = r.connect(config['rdb']['host'], config['rdb']['port'])
        db = r.db('bgeo')
        sq = "(?i)^{0}".format(search)
        locs = list(db.table("locations").filter(lambda doc:
            doc["name"].match(sq)).order_by('name').limit(20).run(c))
        res['found'] = len(locs)
        res['loc_names'] = [l['name'] for l in locs]
        res['result'] = 'success'
    else:
        res['found'] = 0
        res['result'] = 'success'
    return jsonify(res)

@app.route('/bgeo/api/v1.0/location/by-query', methods=['GET'])
def get_location_by_query():
    qparms = request.args
    qName = request.args.get('name')
    qBook = request.args.get('book')
    qChapter = request.args.get('chapter')
    qLimit = request.args.get('limit')
    if not qLimit:
        lim = 50
    c = r.connect(config['rdb']['host'], config['rdb']['port'])
    if qName and qBook and qChapter:
        filters = {'name': qName, 'book': qBook, 'chapter': qChapter}
    else:
        if qName:
            filters = {'name': qName}
        elif qBook and qChapter:
            filters = {'book': qBook, 'chapter': qChapter}
        elif qBook:
            filters = {'book': qBook}
    #lower them all
    for k, v in filters.iteritems():
        filters[k] = v.lower()
    print(filters)
    locs = list(r.db('bgeo').table("locations").filter(filters).limit(lim).run(c))
    geojson = []
    for l in locs:
        # Get references for popup
        xRefs = list(r.db('bgeo').table('references').filter(lambda rl:
                rl['loc_ref'].contains(l['id'])).run(c))
        xPopup = [x['bref'] for x in xRefs]

        if len(xPopup) > 1:
            xPopup = ', '.join(xPopup)
        else:
            xPopup = xPopup[0]
        g = {}
        g['type'] = "Point"
        g['coordinates'] = l['location']['coordinates']
        p = {}
        p['name'] = l['name']
        p['popupContent'] = '{0}: {1}'.format(l['name'], xPopup)
        t = {}
        t['type'] = "Feature"
        t['geometry'] = g
        t['properties'] = p
        geojson.append(t)
    rSize = len(geojson)
    return json.dumps({'rSize': rSize, 'results': geojson})


@app.route('/bgeo/api/v1.0/location/by-name/<lname>', methods=['GET'])
def get_location_by_name(lname):
    if lname is None:
        return 404
    qparms = request.args
    filters = {'name': lname}
    #for k, v in qparms.iteritems:
    #    if k == 'limit':
    #        continue
    #    filters[k] = v
    lim = request.args.get('limit')
    if not lim:
        lim = 50
    c = r.connect(config['rdb']['host'], config['rdb']['port'])
    locs = list(r.db('bgeo').table("locations").filter(filters).limit(lim).run(c))
    geojson = []
    for l in locs:
        # Get references for popup
        xRefs = list(r.db('bgeo').table('references').filter(lambda rl:
                rl['loc_ref'].contains(l['id'])).run(c))
        sortedRefs = sortRefs(xRefs)
        refString = ''
        if len(sortedRefs) > 1:
            refString = '{0}, ... {1}'.format(sortedRefs[0], sortedRefs[-1])
        elif len(sortedRefs) == 1:
            refString = sortedRefs[0]
        else:
            refString = ''
        g = {}
        g['type'] = "Point"
        g['coordinates'] = l['location']['coordinates']
        p = {}
        p['name'] = l['name']
        p['popupContent'] = l['name']
        p['refString'] = refString
        p['lid'] = l['id']
        t = {}
        t['type'] = "Feature"
        t['geometry'] = g
        t['properties'] = p
        geojson.append(t)
    rSize = len(geojson)
    return json.dumps({'rSize': rSize, 'results': geojson})

@app.route('/bgeo/api/v1.0/references/by-locid/<lid>', methods=['GET'])
def get_xrefs_by_locID(lid):
    c = r.connect(config['rdb']['host'], config['rdb']['port'])
    xRefs = list(r.db('bgeo').table('references').filter(lambda rl:
        rl['loc_ref'].contains(lid)).run(c))
    xRefString = ''
    if len(xRefs) >1:
        xRefString = xRefs[0]
    else:
        xRefString = ','.join(xRefs)
    xRefs = [x['bref'] for x in xRefs]
    return render_template('refDetails.html', refs=xRefs)

@app.route('/bgeo/api/v1.0/places/by_name/<pname>', methods=['GET'])
def get_places_by_name(pname):
    print 'stuff'

@app.route('/bgeo/api/v1.0/places/by_proximity/<pid>', methods=['GET'])
def get_places_by_prox(pid):
    print 'stuff'

@app.route('/bgeo/api/v1.0/places', methods=['GET'])
def get_places():
    results = r.table("places").order_by("name").limit(10).run(c)
    places = []
    for res in results:
        places.append(res)

    p = []
    for place in places:
        p.append(place.to_json())
    return jsonify({'result': 'success', 'res': p})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5151, debug=True)
