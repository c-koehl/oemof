# -*- coding: utf-8 -*-

"""
This test contains a ElectricalBus and ElectricalLine class.


This file is part of project oemof (github.com/oemof/oemof). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location
oemof/tests/test_scripts/test_solph/test_variable_chp/test_variable_chp.py

SPDX-License-Identifier: MIT
"""

from nose.tools import eq_
import logging
import pandas as pd

from oemof import outputlib

import oemof.solph as solph
from oemof.solph import custom


def test_lopf(solver="cbc"):
    logging.info("Initialize the energy system")

    # create time index for 192 hours in May.
    date_time_index = pd.date_range("5/5/2012", periods=1, freq="H")
    es = solph.EnergySystem(timeindex=date_time_index)

    ##########################################################################
    # Create oemof.solph objects
    ##########################################################################

    logging.info("Create oemof.solph objects")

    b_el0 = custom.ElectricalBus(label="b_0", v_min=-1, v_max=1)

    b_el1 = custom.ElectricalBus(label="b_1", v_min=-1, v_max=1)

    b_el2 = custom.ElectricalBus(label="b_2", v_min=-1, v_max=1)

    es.add(b_el0, b_el1, b_el2)

    es.add(
        custom.ElectricalLine(
            input=b_el0,
            output=b_el1,
            reactance=0.0001,
            investment=solph.Investment(ep_costs=10),
            min=-1,
            max=1,
        )
    )

    es.add(
        custom.ElectricalLine(
            input=b_el1,
            output=b_el2,
            reactance=0.0001,
            nominal_value=60,
            min=-1,
            max=1,
        )
    )

    es.add(
        custom.ElectricalLine(
            input=b_el2,
            output=b_el0,
            reactance=0.0001,
            nominal_value=60,
            min=-1,
            max=1,
        )
    )

    es.add(
        solph.Source(
            label="gen_0",
            outputs={b_el0: solph.Flow(nominal_value=100, variable_costs=50)},
        )
    )

    es.add(
        solph.Source(
            label="gen_1",
            outputs={b_el1: solph.Flow(nominal_value=100, variable_costs=25)},
        )
    )

    es.add(
        solph.Sink(
            label="load",
            inputs={
                b_el2: solph.Flow(
                    nominal_value=100, actual_value=1, fixed=True
                )
            },
        )
    )

    ##########################################################################
    # Optimise the energy system and plot the results
    ##########################################################################

    logging.info("Creating optimisation model")
    om = solph.Model(es)

    logging.info("Running lopf on 3-Node exmaple system")
    om.solve(solver=solver)

    results = outputlib.processing.results(om)

    generators = outputlib.views.node_output_by_type(results, solph.Source)

    generators_test_results = {
        (es.groups["gen_0"], es.groups["b_0"], "flow"): 20,
        (es.groups["gen_1"], es.groups["b_1"], "flow"): 80,
    }

    for key in generators_test_results.keys():
        logging.debug("Test genertor production of {0}".format(key))
        eq_(
            int(round(generators[key])),
            int(round(generators_test_results[key])),
        )

    eq_(
        results[es.groups["b_2"], es.groups["b_0"]]["sequences"]["flow"][0],
        -40,
    )

    eq_(
        results[es.groups["b_1"], es.groups["b_2"]]["sequences"]["flow"][0], 60
    )

    eq_(
        results[es.groups["b_0"], es.groups["b_1"]]["sequences"]["flow"][0],
        -20,
    )

    # objective function
    eq_(round(outputlib.processing.meta_results(om)["objective"]), 3200)
