import contextlib
import math
import unittest

import xlwings as xw

import xlarith as xa
from xlarith.allocator import ArenaAllocator


class TestEngineXlwingsIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.app = xw.App(visible=False, add_book=True)
            cls._app_pid = cls.app.pid
            cls.app.display_alerts = False
            cls.addClassCleanup(cls._cleanup_excel_app)
        except Exception as exc:  # pragma: no cover - depends on local Excel setup
            raise unittest.SkipTest(f'Excel app is not available: {exc}') from exc

    @classmethod
    def _cleanup_excel_app(cls) -> None:
        app = getattr(cls, 'app', None)
        if app is None:
            return

        # Close books first to avoid save prompts in some Excel configurations.
        with contextlib.suppress(Exception):
            for book in list(app.books):
                book.close()

        with contextlib.suppress(Exception):
            app.quit()

        # As a safety net, kill the exact app process if it still exists.
        app_pid = getattr(cls, '_app_pid', None)
        if app_pid is None:
            return
        for running_app in list(xw.apps):
            if running_app.pid == app_pid:
                running_app.kill()
                break

    def setUp(self) -> None:
        self.app.books.active.sheets.active.cells.clear_contents()
        allocator = ArenaAllocator(start_row=1, start_col=1, max_width=50, gap=1)
        self.engine = xa.Engine(
            self.app,
            allocator=allocator,
        )

    def test_evaluate_vector_expression_via_excel(self) -> None:
        vector = self.engine.create_ref([1, 2, 3])
        result = self.engine.evaluate(vector + 1)

        self.assertEqual(result, [2, 3, 4])

    def test_evaluate_matrix_expression_via_excel(self) -> None:
        left = self.engine.create_ref([[1, 2], [3, 4]])
        right = self.engine.create_ref([[10, 20], [30, 40]])
        result = self.engine.evaluate(left + right)

        self.assertEqual(result, [[11, 22], [33, 44]])

    def test_round_tie_behavior_differs_from_python(self) -> None:
        positive = self.engine.create_ref(2.5)
        negative = self.engine.create_ref(-2.5)

        excel_pos = self.engine.evaluate(xa.wf.round(positive, 0))
        excel_neg = self.engine.evaluate(xa.wf.round(negative, 0))

        self.assertEqual(excel_pos, 3.0)
        self.assertEqual(excel_neg, -3.0)

        # Python uses bankers rounding for ties.
        self.assertEqual(round(2.5), 2)
        self.assertEqual(round(-2.5), -2)

    def test_evaluate_matrix_with_scalar_broadcast_via_excel(self) -> None:
        matrix = self.engine.create_ref([[1, 2], [3, 4]])
        scalar = self.engine.create_ref(10)

        result = self.engine.evaluate(matrix + scalar)

        self.assertEqual(result, [[11, 12], [13, 14]])

    def test_evaluate_materialized_subexpression_via_excel(self) -> None:
        a = self.engine.create_ref(3)
        b = self.engine.create_ref(4)
        partial = self.engine.materialize(a + b)

        result = self.engine.evaluate(partial * 2)

        self.assertEqual(result, 14)

    def test_log_uses_excel_natural_log(self) -> None:
        value = self.engine.create_ref(math.e)

        result = self.engine.evaluate(xa.wf.log(value))

        self.assertAlmostEqual(result, 1.0, places=12)

    def test_log10_uses_excel_base10_log(self) -> None:
        value = self.engine.create_ref(1000)

        result = self.engine.evaluate(xa.wf.log10(value))

        self.assertAlmostEqual(result, 3.0, places=12)

    def test_sum_reduces_vector_to_scalar(self) -> None:
        vector = self.engine.create_ref([1, 2, 3, 4])

        result = self.engine.evaluate(xa.wf.sum(vector))

        self.assertEqual(result, 10)

    def test_product_reduces_vector_to_scalar(self) -> None:
        vector = self.engine.create_ref([2, 3, 4])

        result = self.engine.evaluate(xa.wf.product(vector))

        self.assertEqual(result, 24)

    def test_row_and_column_vector_orientations_broadcast_as_expected(self) -> None:
        row = self.engine.create_ref([1, 2, 3], vector_orientation='row')
        col = self.engine.create_ref([1, 2, 3], vector_orientation='column')

        result = self.engine.evaluate(row + col)

        self.assertEqual(
            result,
            [
                [2, 3, 4],
                [3, 4, 5],
                [4, 5, 6],
            ],
        )


if __name__ == '__main__':
    unittest.main()
