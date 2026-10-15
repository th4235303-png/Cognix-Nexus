from app.services.book_intelligence import parse_json, values


def test_parse_book_reader_json():
    data = parse_json('{"summary":"x","keys":["a"]}')
    assert data["summary"] == "x"
    assert values(data, "keys") == ["a"]


def test_values_rejects_empty_items():
    assert values({"lessons": ["", "useful", 1]}, "lessons") == ["useful", "1"]
