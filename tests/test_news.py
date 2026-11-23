"""Offline tests for milliyet_mcp.news — recorded real milliyet.com.tr pages.

Fixtures are real pages fetched 2026-11-23 (plain curl, browser UA):
- homepage.html: / (93 deduped article links; video/gallery/kids
  links excluded).
- category-gundem.html: /gundem/ (40 articles: slider + list +
  authors slider; 10 with summaries, 9 columnist cards).
- category-ekonomi.html: /ekonomi/ (42 articles).
- sondakika.html: /son-dakika-haberleri/ (14 timed text items in 4
  section boxes: GÜNDEM, EKONOMİ, DÜNYA, AKTÜALİTE; 10 more timed
  items are video/gallery pages and are excluded).
- article.html: siber-suç story 7706106 (Kübra Çelepi, published
  2026-11-23T11:57:00+03:00, 290 words).
- article-dunya.html: ABD siber saldırı story 7706080 (Dilay Hatip,
  253 words).
"""
import os
import unittest

from milliyet_mcp import news as N

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class TestListingParse(unittest.TestCase):
    def test_gundem(self):
        rows = N.parse_listing(_read("category-gundem.html"))
        self.assertEqual(len(rows), 40)
        first = rows[0]
        self.assertEqual(
            first["title"],
            "Silahlı saldırıda hayatını kaybeden Hilal öğretmeni eşi "
            "anlattı! Telefonunu 10 gün sonra açtı, çıkan notlar yürek burktu",
        )
        self.assertTrue(first["url"].endswith("-7706088"))

    def test_gundem_columnist(self):
        rows = N.parse_listing(_read("category-gundem.html"))
        by_author = {r.get("author"): r for r in rows if "author" in r}
        self.assertEqual(len(by_author), 9)
        ozay = by_author["Özay Şendir"]
        self.assertEqual(
            ozay["title"],
            "Özel sektör devlerinin savaş makinesi ve Türkiye modeli",
        )
        self.assertTrue(ozay["url"].startswith(
            "https://www.milliyet.com.tr/yazarlar/ozay-sendir/"))

    def test_ekonomi(self):
        rows = N.parse_listing(_read("category-ekonomi.html"))
        self.assertEqual(len(rows), 42)
        self.assertIn("Bakan Kacır", rows[0]["title"])
        self.assertIn("insansı robot", rows[0]["title"])

    def test_homepage(self):
        rows = N.parse_listing(_read("homepage.html"))
        self.assertEqual(len(rows), 93)
        self.assertEqual(
            rows[0]["title"],
            "İstanbul'daki 50 AVM'ye otopark cezası: Şikayet yağıyor!",
        )

    def test_no_video_gallery_kids(self):
        for name in ("category-gundem.html", "category-ekonomi.html",
                     "homepage.html", "sondakika.html"):
            for r in N.parse_listing(_read(name)):
                self.assertNotIn("/galeri/", r["url"])
                self.assertNotIn("/milliyet-tv/", r["url"])
                self.assertNotIn("/cocuk/", r["url"])

    def test_all_have_url_title(self):
        for name in ("category-gundem.html", "category-ekonomi.html",
                     "homepage.html", "sondakika.html"):
            for r in N.parse_listing(_read(name)):
                # www or uzmanpara subdomain — both are milliyet.com.tr
                self.assertIn("milliyet.com.tr", r["url"])
                self.assertTrue(r["title"])


class TestSondakikaParse(unittest.TestCase):
    def test_count_and_order(self):
        rows = N.parse_sondakika(_read("sondakika.html"))
        self.assertEqual(len(rows), 14)
        first = rows[0]
        self.assertEqual(first["time"], "12:13")
        self.assertEqual(first["section"], "Gündem")
        self.assertEqual(
            first["title"],
            "Silahlı saldırıda hayatını kaybeden Hilal öğretmeni eşi "
            "anlattı! Telefonunu 10 gün sonra açtı, çıkan notlar yürek burktu",
        )
        self.assertTrue(first["url"].endswith("-7706088"))

    def test_sections(self):
        rows = N.parse_sondakika(_read("sondakika.html"))
        self.assertEqual(
            sorted({r["section"] for r in rows}),
            ["Aktüalite", "Dünya", "Ekonomi", "Gündem"],
        )

    def test_times_descending_within_sections(self):
        rows = N.parse_sondakika(_read("sondakika.html"))
        self.assertEqual(rows[1]["time"], "11:57")
        self.assertEqual(rows[2]["time"], "11:27")


class TestArticleParse(unittest.TestCase):
    def setUp(self):
        self.a = N.parse_article(_read("article.html"))

    def test_core(self):
        self.assertEqual(
            self.a["title"],
            "12 ilde siber suç operasyonu! 5 günde 101 şüpheli yakalandı, "
            "60 tutuklama",
        )
        self.assertEqual(self.a["author"], "Kübra Çelepi")
        self.assertEqual(self.a["date_published"], "2026-11-23T11:57:00+03:00")
        self.assertEqual(self.a["date_modified"], "2026-11-23T11:57:38+03:00")
        self.assertEqual(self.a["section"], "Gündem")
        self.assertEqual(self.a["word_count"], 290)

    def test_body(self):
        self.assertEqual(len(self.a["body"]), 1897)
        self.assertIn("101 şüpheli yakalandı", self.a["body"])
        self.assertIn("60'ı", self.a["body"])

    def test_keywords_and_image(self):
        self.assertIn("siber suç", self.a["keywords"])
        self.assertTrue(self.a["image"].startswith("https://image.milimaj.com/"))
        self.assertTrue(self.a["url"].endswith("-7706106"))

    def test_dunya_article(self):
        b = N.parse_article(_read("article-dunya.html"))
        self.assertEqual(b["author"], "Dilay Hatip")
        self.assertEqual(b["section"], "Dünya")
        self.assertEqual(b["word_count"], 253)
        self.assertIn("siber saldırı", b["body"])

    def test_no_body(self):
        with self.assertRaises(ValueError):
            N.parse_article("<html><body>no article here</body></html>")


class TestTrHelpers(unittest.TestCase):
    def test_tr_lower(self):
        self.assertEqual(N.tr_lower("İstanbul"), "istanbul")
        self.assertEqual(N.tr_lower("IĞDIR"), "ığdır")
        self.assertEqual(N.tr_lower("Şoför"), "şoför")

    def test_tr_title(self):
        self.assertEqual(N.tr_title("AKTÜALİTE"), "Aktüalite")
        self.assertEqual(N.tr_title("EKONOMİ"), "Ekonomi")
        self.assertEqual(N.tr_title("GÜNDEM"), "Gündem")


if __name__ == "__main__":
    unittest.main()
