import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
from chempy import Substance
from chempy.util import periodic
import math

import const as cn
import helper

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


def get_fmw(formula):
        substance = Substance.from_formula(formula)
        return substance.mass

def transform_molar_weight():
    cfg= st.session_state.config.user.read_config(cn.TRANSFORM_MOLAR_WEIGHT_ID,'default')
    def show_result():
        text = f"Conversion {cfg['formula_in']} -> {cfg['formula_out']}:"
        st.markdown(text)
        cols = st.columns(2)
        with cols[0]:
            st.text_input(f"Formula weight input ({cfg['formula_in']})", Substance.from_formula(cfg['formula_in']).mass)
            st.text_input("factor", factor)
        with cols[1]:
            st.text_input(f"Formula weight output ({cfg['formula_out']})", Substance.from_formula(cfg['formula_out']).mass)
            st.text_input("Result", result)
    
    with st.form("my_form"):
        factor = 0
        result = ''
        factor = ''
        status = 'ready'
        
        cfg['input_concentration'] = st.number_input("Input concentration (mg/L)")
        id = periodic.symbols.index(cfg['master_element'])
        cfg['master_element'] = st.selectbox("Master element", options = periodic.symbols, index=id)
        cfg['formula_in'] = st.text_input("Chemical formula for concentration input", 'N')
        cfg['formula_out'] = st.text_input("Chemical formula for concentration output", 'NO3')
        submitted = st.form_submit_button("Convert")
        if submitted:
            if (cfg['formula_in'] > '') & (cfg['formula_out'] > ''):
                message = ''
                master_element_key = periodic.symbols.index(cfg['master_element']) + 1
                substance_in = Substance.from_formula(cfg['formula_in'])
                substance_out = Substance.from_formula(cfg['formula_out'])
                
                comp_in = substance_in.composition
                comp_out = substance_out.composition
                if (master_element_key in comp_in and master_element_key in comp_out)==False:
                    message = "Master element must be included in input and output formula, please enter valid compositions"
                    status = 'insufficient'
                if message == '':
                    moles_of_master_element_in = comp_in[master_element_key]
                    moles_of_master_element_out = comp_out[master_element_key]
                    fmw_in = get_fmw(cfg['formula_in'])
                    fmw_out = get_fmw(cfg['formula_out'])
                    factor = (fmw_out / fmw_in) * (moles_of_master_element_in / moles_of_master_element_out)
                    result = cfg['input_concentration'] * factor
                    status = 'done'
            else:
                status = 'insufficient'
                message = "Please enter formula for input and output"
    if status == 'done':
        show_result()
    elif status == 'insufficient':
        helper.flash_text(message, "warning")
    st.session_state.config.user.save_config(cn.TRANSFORM_MOLAR_WEIGHT_ID, 'default', cfg)


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
            st.warning("Please enter concentrations for calcium, magnesium and sodium")


def show_menu():
    set_lang()

    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    MENU_FUNCTIONS = [transform_molar_weight, sar_calculator]
    st.markdown(f"### {menu_action}")
    id = MENU_OPTIONS.index(menu_action)
    MENU_FUNCTIONS[id]()