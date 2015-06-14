# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014, 2015 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from superdesk.tests import TestCase
from apps.publish.blocking_filters.filter_condition import FilterConditionService
from eve.utils import ParsedRequest
import json
import superdesk


class FilterConditionTests(TestCase):

    def setUp(self):
        super().setUp()
        with self.app.app_context():
            self.app.data.insert('archive', [{'_id': '1', 'headline': 'story', 'state': 'fetched'}])
            self.app.data.insert('archive', [{'_id': '2', 'headline': 'prtorque', 'state': 'fetched'}])
            self.app.data.insert('archive', [{'_id': '3', 'urgency': 3, 'state': 'fetched'}])
            self.app.data.insert('archive', [{'_id': '4', 'urgency': 4, 'state': 'fetched'}])
            self.app.data.insert('archive', [{'_id': '5', 'urgency': 2, 'state': 'fetched'}])
            self.app.data.insert('archive', [{'_id': '6', 'state': 'fetched'}])

    def test_mongo_using_like_filter_complete_string(self):
        f = FilterConditionService()
        doc = {'field': 'headline', 'operator': 'like', 'value': 'story'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(1, docs.count())
            self.assertEquals('1', docs[0]['_id'])

    def test_mongo_using_like_filter_partial_string(self):
        f = FilterConditionService()
        doc = {'field': 'headline', 'operator': 'like', 'value': 'tor'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(2, docs.count())
            self.assertEquals('1', docs[0]['_id'])
            self.assertEquals('2', docs[1]['_id'])

    def test_mongo_using_startswith_filter(self):
        f = FilterConditionService()
        doc = {'field': 'headline', 'operator': 'startswith', 'value': 'Sto'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(1, docs.count())
            self.assertEquals('1', docs[0]['_id'])

    def test_mongo_using_endswith_filter(self):
        f = FilterConditionService()
        doc = {'field': 'headline', 'operator': 'endswith', 'value': 'Que'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(1, docs.count())
            self.assertEquals('2', docs[0]['_id'])

    def test_mongo_using_notlike_filter(self):
        f = FilterConditionService()
        doc = {'field': 'headline', 'operator': 'notlike', 'value': 'Que'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(5, docs.count())
            self.assertEquals('1', docs[0]['_id'])

    def test_mongo_using_in_filter(self):
        f = FilterConditionService()
        doc = {'field': 'urgency', 'operator': 'in', 'value': '3,4'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(2, docs.count())
            self.assertEquals('3', docs[0]['_id'])
            self.assertEquals('4', docs[1]['_id'])

    def test_mongo_using_notin_filter(self):
        f = FilterConditionService()
        doc = {'field': 'urgency', 'operator': 'nin', 'value': '2,3,4'}
        f._translate_to_mongo_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            docs = superdesk.get_resource_service('archive').get_from_mongo(req=req, lookup=doc['mongo_translation'])
            self.assertEquals(3, docs.count())
            self.assertEquals('1', docs[0]['_id'])
            self.assertEquals('2', docs[1]['_id'])

    def test_elastic_using_in_filter(self):
        f = FilterConditionService()
        doc = {'field': 'urgency', 'operator': 'in', 'value': '3,4'}
        f._translate_to_elastic_query(doc)
        with self.app.app_context():
            req = ParsedRequest()
            req.args = {'source': json.dumps({'query': {'filtered': {'filter': doc['elastic_translation']}}})}
            #req.args = {'source': json.dumps({'query': {'filtered': {'filter': {'term': {'_id': '1'}}}}})}
            docs = superdesk.get_resource_service('archive').get(req=req, lookup=None)
            self.assertEquals(2, docs.count())
            self.assertEquals('4', docs[0]['_id'])
            self.assertEquals('3', docs[1]['_id'])


    def test_get_operator(self):
        f = FilterConditionService()
        self.assertEquals(f._get_mongo_operator('in'), '$in')
        self.assertEquals(f._get_mongo_operator('nin'), '$nin')
        self.assertEquals(f._get_mongo_operator('like'), '$regex')
        self.assertEquals(f._get_mongo_operator('notlike'), '$not')
        self.assertEquals(f._get_mongo_operator('startswith'), '$regex')
        self.assertEquals(f._get_mongo_operator('endswith'), '$regex')

    def test_get_value(self):
        f = FilterConditionService()
        self.assertEquals(f._get_mongo_value('in', '1,2'), [1,2])
        self.assertEquals(f._get_mongo_value('nin', '3'), ['3'])
        self.assertEquals(f._get_mongo_value('like', 'test'), '.*test.*')
        self.assertEquals(f._get_mongo_value('notlike', 'test'), '.*test.*')
        self.assertEquals(f._get_mongo_value('startswith', 'test'), '/^test/i')
        self.assertEquals(f._get_mongo_value('endswith', 'test'), '/.*test/i')