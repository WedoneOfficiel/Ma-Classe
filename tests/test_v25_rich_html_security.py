import unittest

import server


class RichHTMLSecurityTests(unittest.TestCase):
    def test_removes_scripts_event_handlers_unsafe_links_and_css(self):
        raw = (
            '<p onclick="alert(1)">Texte <img src=x onerror="alert(2)">'
            '<a href="javascript:alert(3)" onclick="alert(4)">lien dangereux</a>'
            '<a href="https://example.com/a" onclick="alert(5)">lien sûr</a>'
            '<span style="color:#ff0000;background-image:url(javascript:alert(6));font-size:1.5em">couleur</span>'
            '</p><script>alert(7)</script><svg onload="alert(8)"></svg>'
        )
        clean = server._sanitize_rich_html(raw)
        self.assertNotIn("<script", clean.lower())
        self.assertNotIn("<svg", clean.lower())
        self.assertNotIn("<img", clean.lower())
        self.assertNotIn("onclick", clean.lower())
        self.assertNotIn("onerror", clean.lower())
        self.assertNotIn("javascript:", clean.lower())
        self.assertNotIn("background-image", clean.lower())
        self.assertIn('href="https://example.com/a"', clean)
        self.assertIn("color:#ff0000", clean)
        self.assertIn("font-size:1.5em", clean)
        self.assertIn("lien dangereux", clean)

    def test_converts_legacy_font_tags_and_escapes_text(self):
        clean = server._sanitize_rich_html('<font size="5">Grand & texte</font><script>secret()</script>')
        self.assertIn('<span style="font-size:1.5em">', clean)
        self.assertIn("Grand &amp; texte", clean)
        self.assertNotIn("secret()", clean)

    def test_sanitizes_all_persisted_rich_fields(self):
        data = {
            "lessons": [{
                "content": '<p onmouseover="alert(1)">Cours</p>',
                "homework": {"instructions": '<img src=x onerror="alert(2)">Consigne'}
            }],
            "submissions": [{"correctionComment": '<script>alert(3)</script>Retour'}]
        }
        result = server._sanitize_rich_data(data)
        self.assertNotIn("onmouseover", result["lessons"][0]["content"])
        self.assertNotIn("onerror", result["lessons"][0]["homework"]["instructions"])
        self.assertNotIn("<script", result["submissions"][0]["correctionComment"].lower())
        self.assertIn("Retour", result["submissions"][0]["correctionComment"])


if __name__ == "__main__":
    unittest.main()
