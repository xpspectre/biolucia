import unittest

from biolucia.helpers import *
from biolucia.model import *
import numpy as np


class ComponentReplaceTestCase(unittest.TestCase):
    def test_constant_subs(self):
        const1 = Constant('y', 75)
        const2 = Rule('y', PiecewiseAnalytic([AnalyticSegment(-inf, inf, 2)]))

        self.assertEqual(const1.subs([const2]), const1)

    def test_rule_subs(self):
        seg1 = AnalyticSegment(0, 10, ex('x + y'))
        seg2 = AnalyticSegment(10, 20, ex('2*x'))
        seg3 = AnalyticSegment(-inf, inf, ex('y*y'))

        x = Rule('x', PiecewiseAnalytic([seg3]))
        y = Constant('y', 2)
        z = Rule('z', PiecewiseAnalytic([seg1, seg2]))

        z_all = z.subs([x, y, z])

        self.assertEqual(z_all.evaluate(0), 6)
        self.assertEqual(z_all.evaluate(12), 8)


class ContainsTestCase(unittest.TestCase):
    def test_rule_contains(self):
        seg1 = AnalyticSegment(-inf, inf, ex('x + y'))
        rule1 = Rule('', PiecewiseAnalytic([seg1]))
        self.assertTrue(rule1.contains('x'))
        self.assertTrue(rule1.contains('y'))
        self.assertFalse(rule1.contains('z'))

        seg2 = AnalyticSegment(0, 10, ex('0'))
        seg3 = AnalyticSegment(10, 90, ex('zz + 10'))
        rule2 = Rule('A', PiecewiseAnalytic([seg2, seg3]))
        self.assertFalse(rule2.contains('x'))
        self.assertTrue(rule2.contains('zz'))
        self.assertFalse(rule2.contains('z'))

    def test_constant_contains(self):
        const = Constant('x', 5)

        self.assertFalse(const.contains('y'))


class TopologicalSortTestCase(unittest.TestCase):
    def test_topological_sort(self):
        seg1 = AnalyticSegment(0, 10, ex('x + y'))
        seg2 = AnalyticSegment(10, 20, ex('2*x'))
        seg3 = AnalyticSegment(-inf, inf, ex('y*y'))

        x = Rule('x', PiecewiseAnalytic([seg3]))
        y = Constant('y', 1)
        z = Rule('z', PiecewiseAnalytic([seg1, seg2]))

        correct = [z, x, y]

        self.assertEqual(Component.topological_sort([x, y, z]), correct)
        self.assertEqual(Component.topological_sort([z, x, y]), correct)


class EvaluateComponentTestCase(unittest.TestCase):
    def test_constant_evaluate(self):
        const = Constant('y', 7.5)
        self.assertEqual(const.evaluate(100), 7.5)

    def test_rule_evaluate(self):
        seg1 = AnalyticSegment(0, 10, ex('x + y'))
        seg2 = AnalyticSegment(10, 20, ex('2*x'))
        z = Rule('z', PiecewiseAnalytic([seg1, seg2]))

        self.assertTrue(isnan(z.evaluate(30)))
        self.assertEqual(z.evaluate(5), ex('x+y'))
        self.assertEqual(z.evaluate(10), ex('2*x'))


def equilibrium_model():
    m = Model()
    m = m.add(Constant('A0', 10))
    m = m.add(Constant('B0', 5))
    m = m.add(State('A', Initial(ex('A0')), [], ODE(PiecewiseAnalytic([AnalyticSegment(0, inf, ex('kr*C-kf*A*B'))]))))
    m = m.add(State('B', Initial(ex('B0')), [], ODE(PiecewiseAnalytic([AnalyticSegment(0, inf, ex('kr*C-kf*A*B'))]))))
    m = m.add(State('C', Initial(ex('0')), [], ODE(PiecewiseAnalytic([AnalyticSegment(0, inf, ex('kf*A*B-kr*C'))]))))
    m = m.add(Constant('kf', 0.5))
    m = m.add(Constant('kr', 0.2))

    return m


class OdeBuildingTestCase(unittest.TestCase):
    def test_function_handles(self):
        m = equilibrium_model()

        system = m.build_odes()

        self.assertTrue(np.array_equal(system.ics(), [10, 5, 0]))
        self.assertTrue(np.array_equal(system.odes(0, system.ics()), [-25, -25, 25]))

        real_jacobian = [[-2.5, -5.0, 0.2], [-2.5, -5.0, 0.2], [2.5, 5.0, -0.2]]
        self.assertTrue(np.array_equal(system.jacobian(0, system.ics()), real_jacobian))
