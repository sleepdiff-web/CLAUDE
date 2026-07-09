from dtc_scout.sources.media import extract_media_url


def test_prefers_hd_video():
    html = (
        '{"video_sd_url":"https:\\/\\/video.cdn\\/sd.mp4?a=1",'
        '"video_hd_url":"https:\\/\\/video.cdn\\/hd.mp4?a=1",'
        '"original_image_url":"https:\\/\\/img.cdn\\/x.jpg"}'
    )
    assert extract_media_url(html) == ("video", "https://video.cdn/hd.mp4?a=1")


def test_falls_back_to_image():
    html = '{"original_image_url":"https:\\/\\/img.cdn\\/creative.jpg?oe=abc"}'
    assert extract_media_url(html) == ("image", "https://img.cdn/creative.jpg?oe=abc")


def test_unicode_escapes_decoded():
    html = '{"video_hd_url":"https:\\/\\/v.cdn\\/x.mp4?p=a\\u0026q=b"}'
    assert extract_media_url(html) == ("video", "https://v.cdn/x.mp4?p=a&q=b")


def test_no_media_returns_none():
    assert extract_media_url("<html>nothing here</html>") is None
    assert extract_media_url("") is None
