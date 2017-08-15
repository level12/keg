from __future__ import absolute_import

from keg.testing import WebBase

from keg_apps.web.app import WebApp


class TestViewRouting(WebBase):
    appcls = WebApp

    def test_route_endpoints(self):
        all_endpoints = sorted(self.app.url_map._rules_by_endpoint.keys())
        routing_endpoints = list(filter(lambda x: x.startswith('routing.'), all_endpoints))
        assert routing_endpoints == [
            'routing.cars:create',
            'routing.cars:delete',
            'routing.cars:edit',
            'routing.cars:list',
            'routing.explicit-route',
            'routing.hello-req',
            'routing.hello-world',
            'routing.hw-rule-default',
            'routing.misc',
            'routing.misc:an-abs-url',
            'routing.misc:two-routes',
            'routing.planes:list',
            'routing.tickets',
            'routing.trucks:list',
            'routing.verb-routing',
            'routing.verb-routing-sub',
        ]

    def test_verb_routing(self):
        resp = self.testapp.get('/verb-routing')
        assert resp.text == 'method get'

        resp = self.testapp.post('/verb-routing')
        assert resp.text == 'method post'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.verb-routing'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/verb-routing'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.verb-routing'

    def test_subclassing(self):
        resp = self.testapp.get('/verb-routing-sub')
        assert resp.text == 'method get'

        resp = self.testapp.post('/verb-routing-sub')
        assert resp.text == 'method post'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.verb-routing-sub'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/verb-routing-sub'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.verb-routing-sub'

    def test_explicit_route(self):
        resp = self.testapp.get('/some-route')
        assert resp.text == 'get some-route'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.explicit-route'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/some-route'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.explicit-route'

    def test_hello_world(self):
        resp = self.testapp.get('/hello-world')
        assert resp.text == 'Hello World'

        resp = self.testapp.get('/hello-world/sam')
        assert resp.text == 'Hello sam'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.hello-world'))
        assert len(rules) == 2

        rule = rules.pop()
        assert rule.rule == '/hello-world'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.hello-world'

        rule = rules.pop()
        assert rule.rule == '/hello-world/<name>'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.hello-world'

    def test_hello_world_defaults(self):
        resp = self.testapp.get('/hwrd')
        assert resp.text == 'Hello RD'

        resp = self.testapp.get('/hwrd/sam')
        assert resp.text == 'Hello sam'

        resp = self.testapp.post('/hwrd')
        assert resp.text == 'post Hello RD'

        resp = self.testapp.post('/hwrd/sam')
        assert resp.text == 'post Hello sam'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.hw-rule-default'))
        assert len(rules) == 2

        rule = rules.pop()
        assert rule.rule == '/hwrd/<name>'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.hw-rule-default'

        rule = rules.pop()
        assert rule.rule == '/hwrd'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.hw-rule-default'

    def test_route_with_required_rule(self):
        self.testapp.get('/hello-req-opt1', status=404)

        resp = self.testapp.get('/hello-req/foo')
        assert resp.text == 'Hello foo'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.hello-req'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/hello-req/<name>'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.hello-req'

    def test_route_plain(self):
        resp = self.testapp.get('/cars/list')
        assert resp.text == 'list'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.cars:list'))
        assert len(rules) == 1
        rule = rules.pop()

        assert rule.rule == '/cars/list'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.cars:list'

    def test_route_method_verb_suffix(self):
        resp = self.testapp.get('/cars/create')
        assert resp.text == 'create get'

        resp = self.testapp.post('/cars/create')
        assert resp.text == 'create post'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.cars:create'))
        assert len(rules) == 2

        rule = rules.pop()
        assert rule.rule == '/cars/create'
        assert rule.methods == {'POST', 'OPTIONS'}
        assert rule.endpoint == 'routing.cars:create'

        rule = rules.pop()
        assert rule.rule == '/cars/create'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.cars:create'

    def test_route_relative(self):
        resp = self.testapp.get('/cars/edit', status=404)

        resp = self.testapp.get('/cars/edit/12')
        assert resp.text == 'form w/ data: 12'

        resp = self.testapp.post('/cars/edit/7')
        assert resp.text == 'update car: 7'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.cars:edit'))
        assert len(rules) == 1

        rule = rules.pop()
        assert rule.rule == '/cars/edit/<int:car_id>'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.cars:edit'

    def test_route_on_http_verb_method(self):
        resp = self.testapp.get('/cars/delete/7')
        assert resp.text == 'delete: 7'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.cars:delete'))
        assert len(rules) == 1

        rule = rules.pop()
        assert rule.rule == '/cars/delete/<int:ident>'
        assert rule.methods == {'GET', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.cars:delete'

    def test_rest_example(self):
        resp = self.testapp.get('/tickets')
        assert resp.text == 'list'

        resp = self.testapp.get('/tickets/5')
        assert resp.text == 'single'

        resp = self.testapp.post('/tickets')
        assert resp.text == 'create'

        resp = self.testapp.put('/tickets/6')
        assert resp.text == 'update'

        resp = self.testapp.patch('/tickets/6')
        assert resp.text == 'partial update'

        resp = self.testapp.delete('/tickets/6')
        assert resp.text == 'delete'

        rules = list(self.app.url_map.iter_rules(endpoint='routing.tickets'))
        assert len(rules) == 2

        rule = rules.pop()
        assert rule.rule == '/tickets'
        assert rule.methods == {'GET', 'POST', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.tickets'

        rule = rules.pop()
        assert rule.rule == '/tickets/<int:ticket_id>'
        assert rule.methods == {'GET', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}
        assert rule.endpoint == 'routing.tickets'

    def test_multiple_class_rules(self):
        resp = self.testapp.get('/misc')
        assert resp.text == 'get'

        resp = self.testapp.get('/misc/foo')
        assert resp.text == 'get'

        resp = self.testapp.get('/misc2')
        assert resp.text == 'get'

        resp = self.testapp.get('/misc2/bar', status=405)

        resp = self.testapp.post('/misc2/bar')
        assert resp.text == 'post'

    def test_abs_route(self):
        resp = self.testapp.get('/an-abs-url')
        assert resp.text == 'found me'

    def test_two_routes(self):
        resp = self.testapp.get('/misc/two-routes/8')
        assert resp.text == '17'
        resp = self.testapp.get('/misc/two-routes/9')
        assert resp.text == '17'

    def test_abstract_class_usage(self):
        resp = self.testapp.get('/trucks/list')
        assert resp.text == 'listing Trucks'

        resp = self.testapp.get('/planes/list')
        assert resp.text == 'listing Planes'

    def test_routing_decorator_class_context(self):
        self.testapp.get('/simple', status=200)

        # Make sure options dict gets passed through correctly by making sure we can POST.
        self.testapp.post('/simple', status=200)

        # make sure the endpoints got set correctly
        assert self.app.view_functions['simple1']
        assert self.app.view_functions['simple2']

    def test_routing_decorator_instance_context(self):
        self.testapp.get('/simple3', status=200)
