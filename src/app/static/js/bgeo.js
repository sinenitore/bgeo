function bgeo_main(){
   var rTable = $('#tbl-results').DataTable({
             "paging": false,
             "order": [[ 1, "desc"]],
             "info": true,
             "searching": false,
             "scrollY": 200
             })

  /*var bibleBooks = []
  for (var i=0;i<bookChaps.length;i++){
      b = bookChaps[i].book
      bibleBooks.push('<option value="' + b + '">' + b + '</option>')
  }
  $('#slBook').html(bibleBooks.join(''))
  $('#slBook').on('change', function(){
      var book = this.value
      var chapters = get_book_chapters(book)
      var output = []
      for (var i=1;i<=chapters;i++){
          output.push('<option value=' + i + '>' + i + '</option>')
      }
      $('#slChapter').empty().html(output.join(''))
  });*/
  outdoorLayer = L.tileLayer( 'https://api.mapbox.com/styles/v1/sinenitore/ciqlrxkiy000bbonjmpmfqjt2/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic2luZW5pdG9yZSIsImEiOiJjaXFscTk0NTkwMDJ5Znlubm8ya2VwZjAyIn0.3CK8ZhjJ6OM4pAZvonDovA', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    subdomains: ['a','b','c']
  })
  satLayer = L.tileLayer( 'https://api.mapbox.com/styles/v1/sinenitore/ciqpmeudd0010bfm90hv3mdyb/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic2luZW5pdG9yZSIsImEiOiJjaXFscTk0NTkwMDJ5Znlubm8ya2VwZjAyIn0.3CK8ZhjJ6OM4pAZvonDovA' , {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'})
  mymap = L.map('mapid', {
      center: [31.77, 35.21],
      zoom: 8,
      layers: [satLayer, outdoorLayer]
  });
  var baseMaps = {
      "Sattelite": satLayer,
      "Outdoor": outdoorLayer
  };
  var bibleWater = {}

  var overlayMaps = {
      "Biblical Water": bibleWater
  }
  var measureControl = new L.Control.Measure({
      primaryLengthUnit: 'miles',
      primaryAreaUnit: 'sqmiles',
      position: 'bottomright',
      activeColor: '#990000',
      completedColor: '#ff3333'
  });
  measureControl.addTo(mymap);
  L.control.layers(baseMaps, overlayMaps).addTo(mymap)
  $('#txtLocName').on("keypress", function(e) {
      if (e.keyCode == 13) {
        get_loc_by_name();
        return false; // prevent the button click from happening
      }
  });
  $('#txtLocName').typeahead({
      minLength: 2,
      limit: 10,
      source: function(query, process){
        return $.get('http://192.168.168.254:5151/bgeo/api/v1.0/be/location/search?query=' + query, function(data){
            return process(data.loc_names)}
        )}
  });
  $("#tbl-results tbody").on('click', 'td', function(){
      var cell = rTable.cell(this)
      var lid = $(cell.node()).attr('data-lid')
      console.log(lid)
      get_refs_by_lid(lid);
  })

}

function onEachFeature(feature, layer) {
    // does this feature have a property named popupContent?
    if (feature.properties && feature.properties.popupContent) {
        layer.bindPopup(feature.properties.popupContent);
    }
}

// getting all the markers at once
function getAllMarkers(map) {

    var allMarkersObjArray = []; // for marker objects
    var allMarkersGeoJsonArray = []; // for readable geoJson markers

    $.each(map._layers, function (ml) {

        if (map._layers[ml].feature) {

            allMarkersObjArray.push(this)
            allMarkersGeoJsonArray.push(JSON.stringify(this.toGeoJSON()))
        }
    })

    console.log(allMarkersObjArray);
    return allMarkersObjArray
}

function updateMapView(){
  var markers = getAllMarkers(mymap)
  var numMarkers = markers.length
  console.log(numMarkers)
  if (numMarkers >= 1){
    var boundPoints = []
    for (var i=0;i < numMarkers;i++){
      boundPoints.push(markers[i].getLatLng())
    }
    console.log(boundPoints)
    if (numMarkers == 1) {
      mymap.panTo(markers[0].getLatLng())
    } else {
      var bounds = new L.LatLngBounds(boundPoints)
      mymap.fitBounds(bounds)
    }
  }
}

function get_books(){
    var books = []
    for (var i=0;i<bookChaps.length;i++){
        books.push(bookChaps[i].book)
    }
    return bookChaps[book]
}

function get_book_chapters(book){
    var chaps = 0;
    for (var i=0;i<bookChaps.length;i++){
        if (bookChaps[i].book == book){
            chaps = bookChaps[i].chapters
            break;
        }
    }
    return chaps
}

function results_to_table(data){
    var t = $('#tbl-results').DataTable();
    var tRows = t.data().length;
    var props = data.properties
    var nCount = tRows + 1
    var htmlString = '<tr><td>'+nCount+'</td><td>'+props.name+'</td><td data-lid="'+props.lid+'">'+props.refString+'</td></tr>'
    var newRow = t.row.add($(htmlString)).draw().id();
    console.log(newRow)
    lCount = nCount;
}

function get_loc_by_name(){
  var lname = $('#txtLocName').val()
  console.log(lname)
  var rurl = 'http://192.168.168.254:5151/bgeo/api/v1.0/location/by-name/'
  var qurl = rurl.concat(lname)
  $.getJSON( qurl, function(data){
      if (data.rSize >= 0){
          //mapAddNewLayer(data.geojson)
          console.log(JSON.stringify(data.results))
          for (var i=0;i<data.rSize;i++){
            var f = data.results[i];
            var mNumber = lCount + 1;
            var numMarker = L.ExtraMarkers.icon({
              icon: 'fa-number',
              number: mNumber,
              markerColor: 'blue'})
            var mk = L.geoJson(data.results[i], {
              pointToLayer: function(feature, latlng){
                 return L.marker(latlng, {icon: numMarker});
              },
              onEachFeature: onEachFeature
            }).addTo(mymap)
            results_to_table(f)
          }
          updateMapView()
          console.log(mk)
      } else {
          alert ( "Location not found." )
      }})
      .fail(function(){
          alert ( "It failed." )
      })
}

function get_refs_by_lid(lid){
  var rurl = 'http://localhost:5151/bgeo/api/v1.0/references/by-locid/'
  var qurl = rurl.concat(lid)
  $.get(qurl, function(data){
     $('#divLocDetails').html(data)
  })
  .success(function(){
      $('.bref').webuiPopover(popOpts)
      console.log('*** calling webuiPopover now ***')
  })
  .fail(function(){
      alert ( "It failed." )
  })
}

$("#btnLocSearch").on('click', function(e){
    e.preventDefault();
    console.log('Caught submission, will call function now')
    get_loc_by_name();
})
var lCount = 0;
var mymap = null;
var refTagger = {
  settings: { 
      bibleVersion: "KJV",
      roundCorners: true,
      socialSharing: [],
      tooltipStyle: "dark",
      tagAutomatically: false,
      convertHyperlinks: true,
  }   
}

/*
$(document.body).on('click', '.bref', function(e){
    e.preventDefault();
    var cTarg = e.target
    var bref = cTarg.text;
    var refText = '';
});
*/

function get_bref_popup(bref){
    var qurl = bapi_url + bref + '?translation=kjv'
    var htmlRes = '';
    $.ajax({
        url: qurl, 
        dataType: 'json',
        async: false,
        success: function(data){
            if (data.error) {
                console.log('Error')
            } else {
                console.log(data['verses'])
                vCount = data['verses'].length
                vs = data.verses
                for (var i=0;i<vs.length;i++){
                  vNum = vs[i].verse
                  vText = vs[i].text
                  htmlRes = htmlRes + vNum + ') ' + vText + '<br>'
                }
                htmlRes = htmlRes.slice(0,-4)
           }
        }
    });
    return htmlRes;
};

var popOpts = {
    animation: 'fade',
    type: 'async',
    delay: {
        show: 300,
        hide: 100
    },
    closeable: true,
    content: function(){
        var bref = $(this).attr('data-bref')
        console.log('BREF in popover = ' + bref)
        var res = get_bref_popup(bref)
        console.log('HTML RES')
        console.log(res)
        return res
    }
}

var bapi_url = 'http://192.168.168.254:5151/proxy/api/v1.0/bible-api/'
var popTemplate = '<div class="popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
var bookChaps = [
    {book: 'Genesis', chapters: 50},
    {book: 'Exodus', chapters: 40},
    {book: 'Leviticus', chapters: 27},
    {book: 'Numbers', chapters: 36},
    {book: 'Dueteronomy', chapters: 34},
    {book: 'Joshua', chapters: 24},
    {book: 'Judges', chapters: 21},
    {book: 'Ruth', chapters: 4},
    {book: 'I Samuel', chapters: 31},
    {book: 'II Samuel', chapters: 24},
    {book: 'I Kings', chapters: 22},
    {book: 'II Kings', chapters: 25},
    {book: 'I Chronicles', chapters: 29},
    {book: 'II Chronicles', chapters: 36},
    {book: 'Ezra', chapters: 10},
    {book: 'Nehemiah', chapters: 13},
    {book: 'Esther', chapters: 10},
    {book: 'Job', chapters: 42},
    {book: 'Psalms', chapters: 150},
    {book: 'Proverbs', chapters: 31},
    {book: 'Ecclesiastes', chapters: 12},
    {book: 'The Song of Songs', chapters: 8},
    {book: 'Isaiah', chapters: 66},
    {book: 'Jeremiah', chapters: 52},
    {book: 'Lamentations', chapters: 5},
    {book: 'Ezekiel', chapters: 48},
    {book: 'Daniel', chapters: 12},
    {book: 'Hosea', chapters: 14},
    {book: 'Joel', chapters: 3},
    {book: 'Amos', chapters: 9},
    {book: 'Obadiah', chapters: 1},
    {book: 'Jonah', chapters: 4},
    {book: 'Micah', chapters: 7},
    {book: 'Nahum', chapters: 3},
    {book: 'Habakkuk', chapters: 3},
    {book: 'Zephaniah', chapters: 3},
    {book: 'Haggai', chapters: 2},
    {book: 'Zechariah', chapters: 14},
    {book: 'Malachi', chapters: 4},
    {book: 'Matthew', chapters: 28},
    {book: 'Mark', chapters: 16},
    {book: 'Luke', chapters: 24},
    {book: 'John', chapters: 21},
    {book: 'Acts', chapters: 28},
    {book: 'Romans', chapters: 16},
    {book: 'I Corinthians', chapters: 16},
    {book: 'II Corinthians', chapters: 13},
    {book: 'Galatians', chapters: 6},
    {book: 'Ephesians', chapters: 6}, 
    {book: 'Philippians', chapters: 4},
    {book: 'Colossians', chapters: 4},
    {book: 'I Thessalonians', chapters: 5},
    {book: 'II Thessalonians', chapters: 3},
    {book: 'I Timothy', chapters: 6},
    {book: 'II Timothy', chapters: 3},
    {book: 'Titus', chapters: 3},
    {book: 'Philemon', chapters: 1},
    {book: 'Hebrews', chapters: 13},
    {book: 'James', chapters: 5},
    {book: 'I Peter', chapters: 5},
    {book: 'II Peter', chapters: 3},
    {book: 'I John', chapters: 5},
    {book: 'II John', chapters: 1},
    {book: 'III John', chapters: 1},
    {book: 'Jude', chapters: 1},
    {book: 'Revelation', chapters: 22}
]
