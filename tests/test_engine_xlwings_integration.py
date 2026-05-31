import unittest

import xlwings as xw

from xlarith.engine import Engine


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
        try:
            for book in list(app.books):
                book.close()
        except Exception:
            pass

        try:
            app.quit()
        except Exception:
            pass

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

    def test_evaluate_vector_expression_via_excel(self) -> None:
        engine = Engine(self.app, start_row=1, start_col=1, max_width=50, gap=1)

        vector = engine.create_ref([1, 2, 3])
        result = engine.evaluate(vector + 1)

        self.assertEqual(result, [2, 3, 4])

    def test_evaluate_matrix_expression_via_excel(self) -> None:
        engine = Engine(self.app, start_row=1, start_col=1, max_width=50, gap=1)

        left = engine.create_ref([[1, 2], [3, 4]])
        right = engine.create_ref([[10, 20], [30, 40]])
        result = engine.evaluate(left + right)

        self.assertEqual(result, [[11, 22], [33, 44]])


if __name__ == '__main__':
    unittest.main()
