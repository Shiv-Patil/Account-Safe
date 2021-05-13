from kivy.uix.recyclegridlayout import RecycleGridLayout

class RecycleGridLayoutFix(RecycleGridLayout):
    def __init__(self, **kwargs):
        super(RecycleGridLayoutFix, self).__init__(**kwargs)

    def compute_visible_views(self, data, viewport):
        if self._cols_pos is None:
            return []
        x, y, w, h = viewport
        right = x + w
        top = y + h
        at_idx = self.get_view_index_at
        # 'tl' is not actually 'top-left' unless 'orientation' is 'lr-tb'.
        # But we can pretend it always is. Same for 'bl' and 'br'.
        tl = at_idx((x, top))
        tr = at_idx((right, top))
        bl = at_idx((x, y))
        br = at_idx((right, y))
        cond1 = not self._fills_from_top_to_bottom
        cond2 = not self._fills_from_left_to_right
        if not self._fills_row_first:
            tr, bl = bl, tr
            cond1, cond2 = cond2, cond1
        if cond1:
            tl, tr, bl, br = bl, br, tl, tr
        if cond2:
            tl, tr, bl, br = tr, tl, br, bl

        n = len(data)
        indices = []
        stride = len(self._cols) if self._fills_row_first else len(self._rows)
        if stride:
            x_slice = br - bl + 1
            for s in range(tl, bl + 1, stride):
                indices.extend(range(min(s, n), min(n, s + x_slice)))
        return indices
