"""Unit tests for the squarified treemap layout."""

from filesearch.core.treemap_layout import layout_treemap


class TestTreemapLayout:
    """Validate deterministic layout geometry."""

    def test_all_rectangles_stay_within_bounds(self):
        """Every rectangle is contained by the provided bounding box."""
        rects = layout_treemap(
            [("alpha", 40), ("beta", 30), ("gamma", 20), ("delta", 10)],
            0,
            0,
            400,
            280,
        )

        assert rects
        for rect in rects:
            assert rect.x >= 0
            assert rect.y >= 0
            assert rect.width >= 0
            assert rect.height >= 0
            assert rect.x + rect.width <= 400.0001
            assert rect.y + rect.height <= 280.0001

    def test_non_empty_items_do_not_produce_invalid_geometry(self):
        """Positive weights should yield non-negative geometry."""
        rects = layout_treemap(
            [("alpha", 5), ("beta", 4), ("gamma", 3)],
            10,
            20,
            240,
            180,
        )

        assert len(rects) == 3
        assert all(rect.width >= 0 for rect in rects)
        assert all(rect.height >= 0 for rect in rects)

    def test_larger_items_receive_larger_areas(self):
        """Area is proportional to item weight."""
        rects = layout_treemap(
            [("large", 60), ("medium", 30), ("small", 10)],
            0,
            0,
            300,
            200,
        )
        areas = {rect.item: rect.width * rect.height for rect in rects}

        assert areas["large"] > areas["medium"] > areas["small"]

    def test_layout_is_deterministic_for_stable_input(self):
        """Repeated calls with the same input produce the same rectangles."""
        items = [("alpha", 8), ("beta", 5), ("gamma", 3)]
        first = layout_treemap(items, 0, 0, 320, 240)
        second = layout_treemap(items, 0, 0, 320, 240)

        first_geometry = [
            (rect.item, rect.x, rect.y, rect.width, rect.height) for rect in first
        ]
        second_geometry = [
            (rect.item, rect.x, rect.y, rect.width, rect.height) for rect in second
        ]
        assert first_geometry == second_geometry
