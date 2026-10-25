"""Candidate regressions plus the27 existing browser checks; all API traffic is mocked."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nova-browser'))
import browser_suite as base
from playwright.sync_api import expect

EXPECTED_TESTS=34
RU={'name':'Как к вам обращаться?','contact':'+998... или @username'}
UZ={'name':'Sizga qanday murojaat qilaylik?','contact':'+998... yoki @username'}


class CandidateTests(base.BrowserTests):
    def placeholders(self,expected):
        for name,text in expected.items():
            expect(self.page.locator('#leadForm [name='+name+']')).to_have_attribute('placeholder',text)

    def test_candidate_initial_uz_placeholders(self):
        self.open('/?lang=uz');self.placeholders(UZ)

    def test_candidate_switch_restores_placeholders_and_keeps_values(self):
        p=self.open('/?lang=ru');self.placeholders(RU)
        form=p.locator('#leadForm');self.fill(form)
        form.locator('[name=notes]').fill('Draft fixture notes')
        for lang,expected in [('uz',UZ),('ru',RU),('uz',UZ),('ru',RU)]:
            p.locator('[data-lang='+lang+']').click();self.placeholders(expected)
            expect(form.locator('[name=name]')).to_have_value('Browser Fixture')
            expect(form.locator('[name=contact]')).to_have_value('TEST_ONLY_NO_DELIVERY')
            expect(form.locator('[name=notes]')).to_have_value('Draft fixture notes')
            expect(form.locator('[name=consent]')).to_be_checked()
        self.assertEqual(self.posts,[])

    def test_candidate_persisted_language_and_explicit_override(self):
        p=self.open('/?lang=uz');self.placeholders(UZ)
        p.goto(base.ORIGIN+'/',wait_until='networkidle');self.placeholders(UZ)
        expect(p.locator('html')).to_have_attribute('lang','uz')
        p.goto(base.ORIGIN+'/?lang=ru',wait_until='networkidle');self.placeholders(RU)
        expect(p.locator('html')).to_have_attribute('lang','ru')
        p.reload(wait_until='networkidle');self.placeholders(RU)

    def test_candidate_keyboard_language_focus(self):
        p=self.open('/?lang=ru');ru=p.locator('[data-lang=ru]');uz=p.locator('[data-lang=uz]')
        ru.focus();ru.press('Tab');expect(uz).to_be_focused()
        style=uz.evaluate('(b)=>({width:getComputedStyle(b).outlineWidth,style:getComputedStyle(b).outlineStyle})')
        self.assertEqual(style,{'width':'3px','style':'solid'})
        uz.press('Enter');self.placeholders(UZ);expect(uz).to_have_attribute('aria-pressed','true')
        uz.press('Shift+Tab');expect(ru).to_be_focused();ru.press('Enter');self.placeholders(RU)


def touch_targets(viewport):
    def check(self):
        p=self.open('/?lang=ru',viewport=viewport)
        for lang,expected in [('uz',UZ),('ru',RU)]:
            button=p.locator('[data-lang='+lang+']');box=button.bounding_box()
            self.assertGreaterEqual(box['width'],44);self.assertGreaterEqual(box['height'],44)
            width,height=p.viewport_size['width'],p.viewport_size['height']
            self.assertGreaterEqual(box['x'],0);self.assertGreaterEqual(box['y'],0)
            self.assertLessEqual(box['x']+box['width'],width);self.assertLessEqual(box['y']+box['height'],height)
            if viewport=='mobile':
                cta=p.locator('.mobile-cta').bounding_box()
                self.assertTrue(box['y']+box['height']<=cta['y'] or cta['y']+cta['height']<=box['y'],'Language target overlaps mobile CTA')
            button.click();self.placeholders(expected)
        self.assertEqual(self.posts,[])
    return check


for viewport in base.VIEWPORTS:
    setattr(CandidateTests,'test_candidate_touch_'+viewport,touch_targets(viewport))
