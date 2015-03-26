from __future__ import absolute_import
from __future__ import unicode_literals
from keg.testing import WebBase

from keg_apps.web.app import WebApp


class TestBaseView(WebBase):
    appcls = WebApp

    def test_route_endpoints(self):
        all_endpoints = sorted(self.app.url_map._rules_by_endpoint.keys())
        assert all_endpoints == [
            u'public.explicit-route',
            u'public.hello-req-opt1',
            u'public.hello-world',
            u'public.hw-rule-default',
            #u'public.routing',
            #u'public.routing-subclass',
            #u'public.routing:create',
            #u'public.routing:delete',
            #u'public.routing:head',
            #u'public.routing:read',
            #u'public.routing:update',
            u'public.template1',
            u'public.template2',
            'public.verb-routing',
            'public.verb-routing-sub',
            'static'
        ]

    def test_verb_routing(self):
        resp = self.testapp.get('/verb-routing')
        assert resp.text == 'method get'

        resp = self.testapp.post('/verb-routing')
        assert resp.text == 'method post'

        rules = list(self.app.url_map.iter_rules(endpoint='public.verb-routing'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/verb-routing'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.verb-routing'

    def test_subclassing(self):
        resp = self.testapp.get('/verb-routing-sub')
        assert resp.text == 'method get'

        resp = self.testapp.post('/verb-routing-sub')
        assert resp.text == 'method post'

        rules = list(self.app.url_map.iter_rules(endpoint='public.verb-routing-sub'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/verb-routing-sub'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.verb-routing-sub'

    def test_explicit_route(self):
        resp = self.testapp.get('/some-route')
        assert resp.text == 'get some-route'

        rules = list(self.app.url_map.iter_rules(endpoint='public.explicit-route'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/some-route'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.explicit-route'

    def test_hello_world(self):
        resp = self.testapp.get('/hello-world')
        assert resp.text == 'Hello World'

        resp = self.testapp.get('/hello-world/sam')
        assert resp.text == 'Hello sam'

        rules = list(self.app.url_map.iter_rules(endpoint='public.hello-world'))
        assert len(rules) == 2

        rule = rules.pop()
        assert rule.rule == '/hello-world'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.hello-world'

        rule = rules.pop()
        assert rule.rule == '/hello-world/<name>'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.hello-world'

    def test_hello_world_defaults(self):
        resp = self.testapp.get('/hwrd')
        assert resp.text == 'Hello RD'

        resp = self.testapp.get('/hwrd/sam')
        assert resp.text == 'Hello sam'

        resp = self.testapp.post('/hwrd')
        assert resp.text == 'post Hello RD'

        resp = self.testapp.post('/hwrd/sam')
        assert resp.text == 'post Hello sam'

        rules = list(self.app.url_map.iter_rules(endpoint='public.hw-rule-default'))
        assert len(rules) == 2

        rule = rules.pop()
        assert rule.rule == '/hwrd/<name>'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.hw-rule-default'

        rule = rules.pop()
        assert rule.rule == '/hwrd'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.hw-rule-default'

    def test_route_with_required_rule(self):
        self.testapp.get('/hello-req-opt1', status=404)

        resp = self.testapp.get('/hello-req-opt1/foo')
        assert resp.text == 'Hello foo'

        rules = list(self.app.url_map.iter_rules(endpoint='public.hello-req-opt1'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/hello-req-opt1/<name>'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'public.hello-req-opt1'

    #def test_multiple_applications(self):
    #    # there is already an application created due to WebBase.setup_class()...create another
    #    # one explicitly.
    #    WebApp(config_profile='TestingProfile').init()
    #    resp = self.testapp.get('/')
    #    assert resp.text == 'get explicit'
    #
    #def test_templating(self):
    #    resp = self.testapp.get('/template1')
    #    assert resp.text == 'Hello world!'
    #
    #def test_custom_name(self):
    #    resp = self.testapp.get('/template2')
    #    assert resp.text == 'template-too'
    #
    #def test_index_route(self):
    #    resp = self.testapp.get('/routing')
    #    assert resp.text == 'read'
    #
    #    rules = list(self.app.url_map.iter_rules(endpoint='public.routing'))
    #    assert len(rules) == 1
    #    rule = rules.pop()
    #
    #    assert rule.rule == '/routing'
    #    assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
    #    assert rule.endpoint == 'public.routing'
    #
    #def test_post_route(self):
    #    resp = self.testapp.get('/routing/create')
    #    assert resp.text == 'create get'
    #
    #    resp = self.testapp.get('/routing/create')
    #    assert resp.text == 'create get'
    #
    #    rules = list(self.app.url_map.iter_rules(endpoint='public.routing:create'))
    #    assert len(rules) == 1
    #    rule = rules.pop()
    #
    #    assert rule.rule == '/routing/create'
    #    assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
    #    assert rule.endpoint == 'public.routing:create'
    #
    #def test_relative_url(self):
    #    resp = self.testapp.get('/routing/update/7', status=405)
    #
    #    resp = self.testapp.post('/routing/update/7')
    #    assert resp.text == 'post update 7'
    #
    #    rules = list(self.app.url_map.iter_rules(endpoint='public.routing:update'))
    #    assert len(rules) == 1
    #    rule = rules.pop()
    #
    #    assert rule.rule == '/routing/update/<int:ident>'
    #    assert rule.methods == {'POST', 'OPTIONS'}
    #    assert rule.endpoint == 'public.routing:update'

    #def test_delete_verb(self):
    #    resp = self.testapp.delete('/routing/123')
    #    assert resp.text == 'delete 123'

    #def test_delete_get(self):
    #    resp = self.testapp.get('/routing/delete/123')
    #    assert resp.text == 'delete 123'
    #
    #def test_head_route(self):
    #    resp = self.testapp.get('/routing/head')
    #    assert resp.text == 'head'
    #
    #def test_route_map(self):
    #    rules = list(self.app.url_map.iter_rules())
    #    return
    #
    #    rule = rules.pop(0)
    #    assert rule.rule == u'/routing/head/head'
    #    assert rule.methods == {'HEAD', 'OPTIONS', 'GET'}
    #    assert rule.endpoint == 'public.routing:head'
    #
    #    rule = rules.pop(0)
    #    assert rule.rule == u'/routing/create'
    #    assert rule.methods == {'HEAD', 'OPTIONS', 'GET', 'POST'}
    #    assert rule.endpoint == 'public.routing:create'
