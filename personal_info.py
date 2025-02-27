import pandas as pd

def load_personal_info():
    # Load the dataset
    personal_info_data = pd.read_excel(r"/Users/purvi/Desktop/boaient/OpenAI model - lifeCare Pilot/lifeEase - Personal Input Sheet.xlsx")
    
    # Group by category and join values
    personal_info_data_grouped = personal_info_data.groupby("Category").agg(lambda x: ' | '.join(x.dropna().astype(str)))
    
    return personal_info_data_grouped.to_dict(orient="index")
