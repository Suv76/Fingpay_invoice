import streamlit as st
import pandas as pd
from io import BytesIO

def process_data(data_file, btcd_file, smfl_file):
    data = pd.read_excel(data_file)
    BTCD = pd.read_excel(btcd_file)
    smfl_data = pd.read_excel(smfl_file, skiprows=3)
    smfl_data = smfl_data.iloc[:-1]

    data['agent_id_login'] = data['Agent Login Id'].str.extract('(\d+)')
    position = data.columns.get_loc('Agent Login Id') + 1
    data.insert(position, 'agent_id_login', data.pop('agent_id_login'))

    data['Branch_code'] = data['Branch Code'].str.extract('(\d+)')
    position = data.columns.get_loc('Branch Code') + 1
    data.insert(position, 'Branch_code', data.pop('Branch_code'))

    non_integer_values = BTCD['Branch ID'].loc[~BTCD['Branch ID'].astype(str).str.isdigit()]
    BTCD['Branch ID'].fillna(0, inplace=True)
    BTCD['Branch ID'] = BTCD['Branch ID'].astype(int, errors='ignore')
    BTCD['Branch ID'] = BTCD['Branch ID'].astype(str)

    merged_data = pd.merge(data, BTCD[['Branch ID', 'State']], left_on='Branch_code', right_on='Branch ID', how='left')
    data['State'] = merged_data['State']
    null_count = data['State'].isnull().sum()

    merged_data1 = pd.merge(data, smfl_data[['Employee_Code', 'State']], left_on='agent_id_login', right_on='Employee_Code', how='left')

    columns_equal = (data['State'] == merged_data1['State_y']).all()

    nan_rows = data['State'].isnull()
    data.loc[nan_rows, 'State'] = merged_data1.loc[nan_rows, 'State_y']

    null_count = data['State'].isnull().sum()

    null_state_rows = data[data['State'].isnull()]
    agent_login_ids = ['Nishanttest', 'nishanttest']
    state_value = 'Karnataka'
    data.loc[data['Agent Login Id'].isin(agent_login_ids), 'State'] = state_value

    data['State'].fillna('Karnataka', inplace=True)
    null_state = data[data['State'].isnull()]

    data['Drop Amount'] = data['Drop Amount'].fillna(0)
    data['Drop Amount'] = data['Drop Amount'].astype(int)

    total_amount = data['Drop Amount'].sum()

    if total_amount <= 150_00_00_000:
        commercial_percentage = 0.0025
    elif total_amount <= 100_00_00_000:
        commercial_percentage = 0.0022
    else:
        commercial_percentage = 0.002

    commercial_value = total_amount * commercial_percentage

    summary_data = {
        'Description': ['Digital Payment', 'Zone_total', '18%', 'Total'],
        'Total': [None, total_amount, None, None],
        'Payout': [60000, commercial_value, commercial_value * 0.18, 60000 + commercial_value + commercial_value * 0.18]
    }
    summary_df = pd.DataFrame(summary_data)

    return data, summary_df

st.title("Invoice Generator")

# Upload files
data_file = st.file_uploader("Upload Samasta CMS Report", type=["xlsx"])
btcd_file = st.file_uploader("Upload BTCD Data", type=["xlsx"])
smfl_file = st.file_uploader("Upload SMFL Data", type=["xlsx"])

# Process data when files are uploaded
if st.button("Generate Invoice") and data_file and btcd_file and smfl_file:
    data, summary_df = process_data(data_file, btcd_file, smfl_file)
    
    # Save to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Data')
        summary_df.to_excel(writer, index=False, sheet_name='Invoice')
    output.seek(0)
    
    # Provide download link
    st.download_button(
        label="Download Invoice",
        data=output,
        file_name='fingpay.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    st.success("Invoice generated successfully!")
