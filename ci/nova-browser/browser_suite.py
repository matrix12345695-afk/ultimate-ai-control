"""Real Chromium frontend checks against exact HTML and intercepted fixture APIs."""
import hashlib
import json
import os
from pathlib import Path
import time
import unittest
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect

ORIGIN='https://nova.test'
VIEWPORTS={'mobile':(360,800),'tablet':(768,1024),'desktop':(1440,900)}
CONCEPTS=('beauty','estate','cafe')
EXPECTED_TESTS=27
EXPECTED_SHOTS=sorted([f'main-{v}-{lang}.png' for v in VIEWPORTS for lang in ('ru','uz')]+[f'{c}-{v}.png' for c in CONCEPTS for v in VIEWPORTS])
SOURCE=None
OUTPUT=None
LOCAL_BROWSER=None
ADVISORIES=set()
BROWSER_VERSION=None


class BrowserTests(unittest.TestCase):
    ENGINE='chromium'
    @classmethod
    def setUpClass(cls):
        global BROWSER_VERSION
        cls.playwright=sync_playwright().start()
        opts={'headless':True}
        if cls.ENGINE=='chromium': opts['args']=['--disable-background-networking']
        if LOCAL_BROWSER: opts['executable_path']=LOCAL_BROWSER
        cls.browser=getattr(cls.playwright,cls.ENGINE).launch(**opts);BROWSER_VERSION=cls.browser.version
    @classmethod
    def tearDownClass(cls): cls.browser.close();cls.playwright.stop()
    def setUp(self): self.context=None;self.page=None;self.posts=[];self.denied=[];self.errors=[]
    def tearDown(self):
        try:
            self.assertEqual(self.denied,[],'Unexpected browser page network request')
            self.assertEqual(self.errors,[],'Uncaught page JavaScript error')
        finally:
            if self.context: self.context.close()
    def open(self,path='/',viewport='desktop',mode='success'):
        width,height=VIEWPORTS[viewport]
        # Firefox supports viewport/touch checks but has no Playwright is_mobile emulation.
        mobile_options={} if self.ENGINE=='firefox' else {'is_mobile':viewport=='mobile'}
        self.context=self.browser.new_context(viewport={'width':width,'height':height},**mobile_options,has_touch=viewport=='mobile',device_scale_factor=1,
                                             reduced_motion='reduce',service_workers='block',accept_downloads=False)
        def handler(route):
            request=route.request;url=urlsplit(request.url)
            if url.scheme!='https' or url.netloc!='nova.test':
                self.denied.append(request.url[:200]);return route.abort()
            if request.method=='GET' and (url.path=='/' or url.path in ('/demo/beauty','/demo/estate','/demo/cafe')):
                return route.fulfill(status=200,content_type='text/html; charset=utf-8',body=(SOURCE/('index.html' if url.path=='/' else 'showcase.html')).read_text())
            if request.method=='GET' and url.path=='/favicon.ico': return route.fulfill(status=204,body='')
            if request.method=='GET' and url.path=='/api/status':
                if mode=='status_failure': return route.abort()
                return route.fulfill(json={'ordersEnabled':mode!='disabled'})
            if request.method=='POST' and url.path=='/api/lead':
                self.posts.append(request.post_data_json)
                if mode=='network': return route.abort()
                return route.fulfill(status=200 if mode=='success' else 503,json={'ok':mode=='success','message':'CI_STUB_ACCEPTED' if mode=='success' else 'CI_STUB_REJECTED'})
            self.denied.append(request.method+' '+request.url[:200]);route.abort()
        self.context.route('**/*',handler)
        self.context.route_web_socket('**',lambda ws:(self.denied.append('websocket'),ws.close()))
        self.page=self.context.new_page();self.page.set_default_timeout(5000)
        self.page.on('pageerror',lambda error:self.errors.append(str(error)[:300]))
        self.page.goto(ORIGIN+path,wait_until='networkidle')
        self.page.add_style_tag(content='*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}html{scroll-behavior:auto!important}')
        return self.page
    def layout(self,selectors):
        page=self.page;width=page.viewport_size['width']
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width+1,'Horizontal page overflow')
        for selector in selectors:
            for element in page.locator(selector).all():
                if not element.is_visible(): continue
                box=element.bounding_box();self.assertIsNotNone(box)
                self.assertGreaterEqual(box['x'],-1,selector+' starts offscreen')
                self.assertLessEqual(box['x']+box['width'],width+1,selector+' extends offscreen')
        self.assertEqual(self.posts,[])
    def shot(self,name):
        path=OUTPUT/name;self.page.screenshot(path=str(path),full_page=True,animations='disabled')
        self.assertTrue(1000<path.stat().st_size<=3*1024**2)
    def fill(self,form):
        form.locator('[name=name]').fill('Browser Fixture')
        form.locator('[name=contact]').fill('TEST_ONLY_NO_DELIVERY')
        form.locator('[name=consent]').check()
    def test_language_persistence(self):
        p=self.open();original=p.locator('h1').inner_text()
        p.locator('[data-lang=uz]').click();expect(p.locator('html')).to_have_attribute('lang','uz')
        self.assertNotEqual(p.locator('h1').inner_text(),original)
        p.reload(wait_until='networkidle');expect(p.locator('[data-lang=uz]')).to_have_attribute('aria-pressed','true')
        expect(p.locator('html')).to_have_attribute('lang','uz')
        p.locator('[data-lang=ru]').click();expect(p.locator('html')).to_have_attribute('lang','ru')
        self.assertEqual(p.locator('h1').inner_text(),original)
    def test_navigation_and_keyboard(self):
        p=self.open();link=p.locator('nav a[href="#services"]');link.focus();link.press('Enter')
        expect(p).to_have_url(ORIGIN+'/?lang=ru#services');expect(p.locator('#services h2')).to_be_in_viewport()
        p.locator('nav a[href="#contact"]').click();expect(p.locator('#leadForm')).to_be_in_viewport()
        p.locator('#leadForm [name=name]').focus();expect(p.locator('#leadForm [name=name]')).to_be_focused()
        links=p.locator('.portfolio-case a').all()
        self.assertEqual(len(links),3)
        self.assertEqual({x.get_attribute('href') for x in links},{'https://novaweb-agency.onrender.com/demo/'+c for c in CONCEPTS})
    def test_main_required(self):
        p=self.open();p.locator('#submitLead').click();self.assertFalse(p.locator('#leadForm').evaluate('(f)=>f.checkValidity()'));self.assertEqual(self.posts,[])
    def test_main_success_once(self):
        p=self.open('/?utm_source=ci&utm_campaign=browser');form=p.locator('#leadForm');self.fill(form)
        p.evaluate('document.querySelector("#submitLead").click();document.querySelector("#submitLead").click()')
        expect(p.locator('#leadStatus')).to_have_text('CI_STUB_ACCEPTED');self.assertEqual(len(self.posts),1)
        self.assertEqual(self.posts[0]['source'],'ci');self.assertEqual(self.posts[0]['campaign'],'browser');self.assertIs(self.posts[0]['consent'],True)
        expect(form.locator('[name=name]')).to_have_value('');expect(p.locator('#submitLead')).to_be_enabled()
    def main_error(self,mode,text):
        p=self.open(mode=mode);form=p.locator('#leadForm');self.fill(form);p.locator('#submitLead').click()
        expect(p.locator('#leadStatus')).to_have_text(text);expect(p.locator('#submitLead')).to_be_enabled()
        expect(form.locator('[name=name]')).to_have_value('Browser Fixture');self.assertEqual(len(self.posts),1)
    def test_main_error(self): self.main_error('error','CI_STUB_REJECTED')
    def test_main_network(self): self.main_error('network','Не удалось отправить. Повторите попытку.')
    def test_main_disabled(self):
        p=self.open(mode='disabled');expect(p.locator('#submitLead')).to_be_disabled();expect(p.locator('#leadStatus')).to_contain_text('Приём заявок');self.assertEqual(self.posts,[])
    def test_main_status_failure(self):
        p=self.open(mode='status_failure');expect(p.locator('#leadStatus')).to_contain_text('Не удалось проверить');self.assertEqual(self.posts,[])
    def test_demo_required(self):
        p=self.open('/demo/beauty');form=p.locator('#contactForm');form.locator('button[type=submit]').click()
        self.assertFalse(form.evaluate('(f)=>f.checkValidity()'));self.assertEqual(self.posts,[])
    def test_demo_success(self):
        p=self.open('/demo/estate?utm_source=ci-demo&utm_campaign=browser');p.locator('.tile button').first.click()
        expect(p.locator('#selected')).to_contain_text('Skyline Residence')
        form=p.locator('#contactForm');self.fill(form);form.locator('button[type=submit]').click()
        expect(p.locator('#status')).to_have_text('CI_STUB_ACCEPTED');self.assertEqual(len(self.posts),1)
        self.assertIn('Skyline Residence',self.posts[0]['notes']);self.assertEqual(self.posts[0]['source'],'ci-demo')
        expect(form.locator('[name=name]')).to_have_value('')
    def demo_error(self,mode,text):
        p=self.open('/demo/cafe',mode=mode);form=p.locator('#contactForm');self.fill(form);form.locator('button[type=submit]').click()
        expect(p.locator('#status')).to_have_text(text);expect(form.locator('button[type=submit]')).to_be_enabled()
        expect(form.locator('[name=name]')).to_have_value('Browser Fixture');self.assertEqual(len(self.posts),1)
    def test_demo_error(self): self.demo_error('error','CI_STUB_REJECTED')
    def test_demo_network(self): self.demo_error('network','Ошибка соединения. Попробуйте снова.')


def main_layout(viewport,language):
    def check(self):
        p=self.open('/?lang='+language,viewport=viewport);expect(p.locator('html')).to_have_attribute('lang',language)
        expect(p.locator(f'[data-lang={language}]')).to_have_attribute('aria-pressed','true')
        self.layout(('header','.hero h1','.card','#leadForm','#leadForm input:not([name=website])','#leadForm select','#leadForm textarea','#submitLead'))
        if viewport=='mobile':
            expect(p.locator('.mobile-cta')).to_be_visible();p.locator('.mobile-cta').click();expect(p.locator('#leadForm')).to_be_in_viewport()
            self.assertGreaterEqual(p.locator('.mobile-cta').bounding_box()['height'],44)
            for element in p.locator('[data-lang]').all():
                box=element.bounding_box()
                if min(box['width'],box['height'])<44: ADVISORIES.add('Language switch targets are smaller than44 CSS px; full touch accessibility remains pending.')
        if language=='uz' and 'Как к вам' in p.locator('[name=name]').get_attribute('placeholder'):
            ADVISORIES.add('UZ page keeps Russian input placeholders; localization coverage is partial.')
        p.evaluate('window.scrollTo(0,0)');self.shot(f'main-{viewport}-{language}.png')
    return check


def demo_layout(concept,viewport):
    def check(self):
        p=self.open('/demo/'+concept,viewport=viewport)
        expect(p.locator('body')).to_have_class(concept);expect(p.locator('.tile')).to_have_count(4)
        self.layout(('header','h1','.tile','#contactForm','#contactForm input:not([type=checkbox])','#contactForm select'))
        p.locator('#filters button').nth(1).click();expect(p.locator('.tile')).to_have_count(2)
        expect(p.locator('#filters button').nth(1)).to_have_attribute('aria-pressed','true')
        p.locator('.tile button').first.click();expect(p.locator('#selected')).not_to_have_text('Вдохновение: выбранный концепт')
        p.locator('#filters button').first.click();expect(p.locator('.tile')).to_have_count(4)
        p.evaluate('window.scrollTo(0,0)');self.shot(f'{concept}-{viewport}.png')
    return check


for v in VIEWPORTS:
    for language in ('ru','uz'): setattr(BrowserTests,'test_layout_main_'+v+'_'+language,main_layout(v,language))
    for concept in CONCEPTS: setattr(BrowserTests,'test_layout_demo_'+concept+'_'+v,demo_layout(concept,v))
