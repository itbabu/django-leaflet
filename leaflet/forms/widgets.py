# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core import validators
from django.template.defaultfilters import slugify
try:
    from django.contrib.gis.forms.widgets import BaseGeometryWidget
except ImportError:
    from .backport import BaseGeometryWidget

from leaflet import app_settings, PLUGINS, PLUGIN_FORMS


class LeafletWidget(BaseGeometryWidget):
    template_name = 'leaflet/widget.html'
    map_srid = 4326
    map_width = None
    map_height = None
    modifiable = True
    supports_3d = False
    include_media = False

    @property
    def media(self):
        if not self.include_media:
            return forms.Media()

        # We assume that including media for widget means there is
        # no Leaflet at all in the page.
        js = ['leaflet/leaflet.js'] + PLUGINS[PLUGIN_FORMS]['js']
        css = ['leaflet/leaflet.css'] + PLUGINS[PLUGIN_FORMS]['css']
        return forms.Media(js=js, css={'screen': css})

    def serialize(self, value):
        return value.geojson if value else ''

    def render(self, name, value, attrs=None):
        assert self.map_srid == 4326, 'Leaflet vectors should be decimal degrees.'

        value = None if value in validators.EMPTY_VALUES else value

        # Retrieve params from Field init (if any)
        self.geom_type = self.attrs.get('geom_type', self.geom_type)

        # Setting 'loadevent' added in the widget constructor
        loadevent = self.attrs.get('loadevent', app_settings.get('LOADEVENT'))

        attrs = attrs or {}

        # In BaseGeometryWidget, geom_type is set using gdal, and fails with generic.
        # See https://code.djangoproject.com/ticket/21021
        if self.geom_type == 'GEOMETRY':
            attrs['geom_type'] = 'Geometry'

        map_id = slugify(attrs.get('id', name)).replace('-', '_')  # JS-safe
        attrs.update(id=map_id,
                     module='geodjango_%s' % map_id,
                     id_map=map_id + '_map',
                     id_map_callback=map_id + '_map_callback',
                     loadevent=loadevent,
                     modifiable=self.modifiable,
                     target_map=attrs.get('target_map', getattr(self, 'target_map', None)),
                     geometry_field_class=attrs.get('geometry_field_class', getattr(self, 'geometry_field_class', 'L.GeometryField')),
                     field_store_class=attrs.get('field_store_class', getattr(self, 'field_store_class', 'L.FieldStore')))
        return super(LeafletWidget, self).render(name, value, attrs)
