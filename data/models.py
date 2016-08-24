from mongoengine import *
from config import config

connect('bgeo', host=config['mongo']['host'], port=config['mongo']['port'])

class PlaceGeometryDoc(EmbeddedDocument):
	type			= StringField()
	coordinates		= PointField

	meta = {
		'indexes': [('coordinates', '2dsphere')]
	}

class PlacePropertiesDoc(EmbeddedDocument):
	begin			= StringField()
	altitudeMode	= StringField()
	end				= StringField()
	name			= StringField()
	description		= StringField()
	tessellate		= IntField()
	extrude			= IntField()
	visibility		= IntField()
	drawOrder		= StringField()
	icon			= StringField()

	meta = {
		'indexes': [('name')]
	}

class ReferenceDoc(EmbeddedDocument):
	bookName		= StringField()
	bookNumber		= IntField()
	chapter			= IntField()
	verse			= IntField()

	meta = {
		'indexes': [('bookName'), ('chapter')]
	}

	
class PlaceDoc(Document):
	geometry		= EmbeddedDocumentField(PlaceGeometryDoc)
	properties		= EmbeddedDocumentField(PlacePropertiesDoc)
	name			= StringField()
	ref				= EmbeddedDocumentField(ReferenceDoc)
