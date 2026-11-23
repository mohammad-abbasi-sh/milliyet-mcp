"""Live tests for milliyet_mcp — real requests to milliyet.com.tr.

Requires network + Chrome TLS impersonation (curl-cffi). The server
is polite by design (~0.8s between requests), so this file takes
~20s. Run: python -m unittest discover -s tests -v

Headlines change during the day; tests assert structure and sane
ranges, not exact titles.
"""
import unittest

from milliyet_mcp import http as H
from milliyet_mcp import news as N


class TestLiveHeadlines(unittest.TestCase):
    def test_gundem(self):
        html_text = H.fetch_category_html("gundem")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 20)
        self.assertIn("milliyet.com.tr", rows[0]["url"])

    def test_ekonomi(self):
        html_text = H.fetch_category_html("ekonomi")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 20)

    def test_dunya(self):
        html_text = H.fetch_category_html("dunya")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 10)

    def test_skorer(self):
        html_text = H.fetch_category_html("skorer")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 10)

    def test_unknown_category_404(self):
        with self.assertRaises(H.MilliyetError):
            H.fetch_category_html("xyzabcqwerty")


class TestLiveLatest(unittest.TestCase):
    def test_sondakika(self):
        html_text = H.fetch_sondakika_html()
        rows = N.parse_sondakika(html_text)
        self.assertGreater(len(rows), 5)
        self.assertRegex(rows[0]["time"], r"^\d{2}:\d{2}$")
        self.assertTrue(rows[0]["title"])


class TestLiveArticle(unittest.TestCase):
    def test_siber_suc(self):
        html_text = H.fetch_article_html(
            "https://www.milliyet.com.tr/gundem/12-ilde-siber-suc-operasyonu-"
            "5-gunde-101-supheli-yakalandi-60-tutuklama-7706106"
        )
        a = N.parse_article(html_text)
        self.assertEqual(
            a["title"],
            "12 ilde siber suç operasyonu! 5 günde 101 şüpheli yakalandı, "
            "60 tutuklama",
        )
        self.assertEqual(a["author"], "Kübra Çelepi")
        self.assertGreater(a["word_count"], 200)

    def test_unknown_article_404(self):
        with self.assertRaises(H.MilliyetError):
            H.fetch_article_html(
                "https://www.milliyet.com.tr/gundem/boyle-bir-haber-yok-0000000"
            )


class TestLiveHealth(unittest.TestCase):
    def test_health_ok(self):
        result = H.health_check()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["http_status"], 200)


if __name__ == "__main__":
    unittest.main()
