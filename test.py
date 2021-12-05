import pandas as pd
from pandas.api.types import is_numeric_dtype

df = pd.DataFrame({'A':['1','5.5','0.12','<0.3','0,4','5','neg.','7', '<0',9,87]})

df['A'] = df['A'].astype(str)

df['D'] =pd.to_numeric(df['A'],errors='coerce')
df['B']=False
df.loc[df['A'].str.startswith('<')==True,'B'] = True
df.loc[df['A'].str.startswith('<')==True,'C'] = df['A'].str.replace('<', '')
df.loc[df['A'].str.isnumeric()==True,'C'] = df['A']
df['C'] = df['C'].astype('float') 
df.loc[(df['B']==True) & (df['C']!= 0),'C'] = df['C'] / 2
print(df)
#self.row_value_df.loc[self.row_value_df[qual_val_col].str.isnumeric(),'_value'] = self.row_value_df[qual_val_col].str.replace('<', '').astype("float")
        