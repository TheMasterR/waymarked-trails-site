# This file is part of waymarkedtrails.org
# Copyright (C) 2016 Sarah Hoffmann
#
# This is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from collections import OrderedDict
from math import isnan
import cherrypy
from sqlalchemy import func
from geoalchemy2.elements import WKTElement
from db.common import route_types as rt

class RouteDict(OrderedDict):

    def __init__(self, db_entry):
        super().__init__(self)
        self['type'] = db_entry['type'] if db_entry.has_key('type') else 'relation'
        self['id'] = db_entry['id']
        if 'ref' in db_entry:
            self.add_if('ref', db_entry['ref'])

        for l in cherrypy.request.locales:
            if l in db_entry['intnames']:
                self['name'] = db_entry['intnames'][l]
                if self['name'] != db_entry['name']:
                    self['local_name'] = db_entry['name']
                break
            else:
                self.add_if('name', db_entry['name'])
        self['group'] = self.get_network(db_entry)
        if 'symbol' in db_entry:
            self['symbol_id'] = str(db_entry['symbol'])

    def add_if(self, key, value):
        if value:
            self[key] = value

    def get_network(self, db_entry):
        if db_entry.has_key('network') and db_entry['network'] is not None:
            return db_entry['network']

        return rt.Network.from_int(db_entry['level']).name


class Bbox(object):

    def __init__(self, value):
        if isinstance(value, tuple):
            self.coords = value
        else:
            parts = value.split(',')
            if len(parts) != 4:
                raise cherrypy.HTTPError(400, "No valid map area specified. Check the bbox parameter in the URL.")
            try:
                self.coords = tuple([float(x) for x in parts])
            except ValueError:
                raise cherrypy.HTTPError(400, "Invalid coordinates given for the map area. Check the bbox parameter in the URL.")
            if any(isnan(f) for f in self.coords):
                raise cherrypy.HTTPError(400, "Invalid coordinates given for the map area. Check the bbox parameter in the URL.")

    def as_sql(self):
        return func.ST_SetSrid(func.ST_MakeBox2D(
                    WKTElement('POINT(%f %f)' % self.coords[0:2]),
                    WKTElement('POINT(%f %f)' % self.coords[2:4])), 3857)

    def center_as_sql(self):
        return func.ST_SetSrid(WKTElement('POINT(%f %f)' %
                                ((self.coords[2] + self.coords[0])/2,
                                 (self.coords[1] + self.coords[3])/2)), 3857)

