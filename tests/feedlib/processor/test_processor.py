from pathlib import Path

import pytest

from rssant_feedlib.processor import (
    story_readability,
    normalize_url,
    validate_url,
    get_html_redirect_url,
    story_extract_attach,
)

_data_dir = Path(__file__).parent.parent / 'testdata/processor'


def _read_text(filename):
    filepath = _data_dir / filename
    return filepath.read_text()


def test_story_readability():
    """
    readability + lxml 4.5.0 has issue:
        readability.readability.Unparseable: IO_ENCODER
    """
    html = _read_text('test_sample.html')
    story_readability(html)


def test_normalize_invalid_url():
    urls_text = _read_text('test_normalize_url.txt')
    urls = list(urls_text.strip().splitlines())
    for url in urls:
        norm_url = normalize_url(url)
        if url.startswith('urn:') or url.startswith('magnet:'):
            assert norm_url == url
        else:
            assert validate_url(norm_url) == norm_url


def test_normalize_url():
    cases = [
        (None, ''),
        ('hello world', 'hello world'),
        ('你好世界', '你好世界'),
        ('2fd1ca54895', '2fd1ca54895'),
        ('www.example.com', 'http://www.example.com'),
        ('://www.example.com', 'http://www.example.com'),
        ('http://example.comblog', 'http://example.com/blog'),
        ('http://example.com//blog', 'http://example.com/blog'),
        ('http://example.com%5Cblog', 'http://example.com/blog'),
        ('http://example.com%5Cblog/hello', 'http://example.com/blog/hello'),
        ('http%3A//www.example.com', 'http://www.example.com'),
        ('http://www.example.com:80', 'http://www.example.com'),
        ('https://www.example.com:443', 'https://www.example.com'),
        (
            'http://www.example.comhttp://www.example.com/hello',
            'http://www.example.com/hello'
        ),
        (
            'http://www.example.com/white space',
            'http://www.example.com/white%20space'
        ),
    ]
    for url, expect in cases:
        norm = normalize_url(url)
        assert norm == expect, f'url={url!r} normalize={norm!r} expect={expect!r}'


def test_normalize_base_url():
    base_url = 'http://blog.example.com/feed.xml'
    url = '/post/123.html'
    r = normalize_url(url, base_url=base_url)
    assert r == 'http://blog.example.com/post/123.html'
    url = 'post/123.html'
    r = normalize_url(url, base_url=base_url)
    assert r == 'http://blog.example.com/post/123.html'
    url = '/'
    r = normalize_url(url, base_url=base_url)
    assert r == 'http://blog.example.com/'


def test_normalize_quote():
    base = 'http://blog.example.com'
    base_url = 'http://blog.example.com/feed.xml'
    path_s = [
        '/post/2019-01-10-%E5%AF%BB%E6%89%BE-sourcetree-%E6%9B%BF%E4%BB%A3%E5%93%81/',
        '/notes/%E8%9A%81%E9%98%85%E6%80%A7%E8%83%BD%E4%BC%98%E5%8C%96%E8%AE%B0%E5%BD%95',
    ]
    for p in path_s:
        r = normalize_url(p, base_url=base_url)
        assert r == base + p


@pytest.mark.parametrize('filename', [
    'html_redirect/test_html_redirect_1.html',
    'html_redirect/test_html_redirect_2.html',
    'html_redirect/test_html_redirect_3.html',
])
def test_get_html_redirect_url(filename):
    base_url = 'https://blog.example.com'
    expect = 'https://blog.example.com/html-redirect/'
    html = _read_text(filename)
    got = get_html_redirect_url(html, base_url=base_url)
    assert got == expect


def test_story_extract_attach_iframe():
    html = _read_text('test_iframe.html')
    attach = story_extract_attach(html)
    expect = 'https://player.bilibili.com/player.html?aid=75057811'
    assert attach.iframe_url == expect


def test_story_extract_attach_audio():
    html = _read_text('test_audio.html')
    attach = story_extract_attach(html)
    expect = 'https://chtbl.com/track/r.typlog.com/pythonhunter/8417630310_189758.mp3'
    assert attach.audio_url == expect


def test_story_extract_attach_audio_source():
    html = '''
    <div>
    <p><strong>直接播放</strong>:</p>
    <audio controls preload style="width:80%;margin-left:34px">
    <source src="/static/2020-07-12/podcast-rssant-parttime-product.mp3?controls=1" type="audio/mpeg">
    <p>你的浏览器不支持播放音频，你可以
    <a href="/static/2020-07-12/podcast-rssant-parttime-product.mp3?controls=1">
    下载</a>这个音频文件。</p></audio>
    </div>
    '''
    base_url = 'https://blog.guyskk.com'
    attach = story_extract_attach(html, base_url=base_url)
    expect = '/static/2020-07-12/podcast-rssant-parttime-product.mp3?controls=1'
    assert attach.audio_url == base_url + expect
