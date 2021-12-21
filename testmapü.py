import numpy as np

class xMap:
    def __init__(self, a):
        self.a = a

        
    def wgs84_to_web_mercator_df(self, df, lat, lon):
        k = 6378137
        df["x"] = df[lon] * (k * np.pi/180.0)
        df["y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k

        return df
    
    def doit(self):
        a = self.a
