import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
from chempy import Substance
import math

import const as cn

text = {}

def get_fmw(formula):
        substance = Substance.from_formula(formula)
        return substance.mass

def transform_molar_weight():
    def show_result():
        text = f"Conversion {formula_in} -> {formula_out}:"
        st.markdown(text)
        cols = st.columns(2)
        with cols[0]:
            st.text_input(f"Formula weight ({formula_in})", Substance.from_formula(formula_in).mass)
            st.text_input("factor", factor)
        with cols[1]:
            st.text_input(f"Formula weight ({formula_out})", Substance.from_formula(formula_out).mass)
            st.text_input("Result", result)

    with st.form("my_form"):
        factor = 0
        result = ''
        factor = ''
        status = 'ready'
        input_concentration = st.number_input("Input concentration (mg/L)")
        formula_in = st.text_input("Chemical formula for concentration input", 'N')
        formula_out = st.text_input("Chemical formula for concentration output", 'NO3')
        submitted = st.form_submit_button("Convert")
        if submitted:
            if (formula_in > '') & (formula_out > ''):
                fmw_in = get_fmw(formula_in)
                fmw_out = get_fmw(formula_out)
                factor = fmw_out / fmw_in
                result = input_concentration * factor
                status = 'done'
            else:
                status = 'insufficient'
    
    if status == 'done':
        show_result()
    elif status == 'insufficient':
        st.warning("Please enter formula for input and output")


def sar_calculator():
    """todo: calculate adjusted SAR using bicarbonate
    """
    def get_sar_interpretation_df():
        """from http://turf.okstate.edu/water-quality/sar-calculator, todo: add reference

        Returns:
            [type]: [description]
        """
        df = pd.DataFrame({
                            'adj SAR': ['<1', '1-2', '2-4', '4-8', '8-15','>15'],
                            'Classification': ['Excellent','Good', 'Fair', 'Poor', 'Very Poor', 'Unnacceptable'],
                            'Management Considerations':['None',
                                                        'Little concern, add pelletized gypsum periodically',
                                                        'Aerify soil, sand topdress, apply pelletized gypsum, monitor soil salinity',
                                                        'Aerify soil, sand topdress, apply pelletized gypsum, leach soil regularly, monitor soil salinity closely',
                                                        'Requires special attention; consult water quality specialist',
                                                        'Do not use']
                          })
        return df

    def get_sar_classification(result):
        """classification from http://turf.okstate.edu/water-quality/sar-calculator
        """
        if result < 1:
            return 'Excellent'
        elif result >= 1 and result < 2:
            return 'Good'
        elif result >= 2 and result < 4:
            return 'Fair'
        elif result >= 4 and result < 8:
            return 'Poor'
        elif result >= 8 and result < 15:
            return 'Very Poor'
        elif result >= 15:
            return 'Unacceptable'

    def show_result(result):
        st.text_input("SAR", f"{result:.1f}")
        st.text_input("Classification", get_sar_classification(result))
        df = get_sar_interpretation_df()
        st.markdown("SAR Classificatio ([reference](http://turf.okstate.edu/water-quality/sar-calculator))")
        AgGrid(get_sar_interpretation_df())

    cols = st.columns(2)
    with cols[0]:
        with st.form("my_form"):
            ec = 0
            ca = 0
            mg = 0
            na = 0
            hco3 = 0
            status = 'ready'
            ec = st.number_input("EC (μS/cm")
            ca = st.number_input("Ca mg/L")
            mg = st.number_input("Mg mg/L")
            na = st.number_input("Na mg/L")
            hco3 = st.number_input("HCO3 mg/L")

            submitted = st.form_submit_button("Calculate")
            if submitted:
                if (na > 0 and ca > 0 and mg > 0):
                    na_meq = na / Substance.from_formula('Na').mass
                    ca_meq = ca / Substance.from_formula('Ca').mass * 2
                    mg_meq = mg / Substance.from_formula('Mg').mass * 2
                    result = na_meq / math.sqrt(0.5*(ca_meq + mg_meq))
                    status = 'done'
                else:
                    status = 'insufficient'
        
        if status == 'done':
            show_result(result)
        elif status == 'insufficient':
            st.warning("Please enter formula for input and output")


def show_menu(texts_dict: dict):
    global text

    text = texts_dict
    menu_options = text['menu_options']
    menu_action = st.sidebar.selectbox('Options', menu_options)
    if menu_action == menu_options[0]:
        with st.expander('Intro'):
            st.markdown(text[menu_action])
        transform_molar_weight()
    if menu_action == menu_options[1]:
        with st.expander('Intro'):
            st.markdown(text[menu_action])
        sar_calculator()