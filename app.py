import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import easyocr

path = st.file_uploader("Select Underdog Battle Royale draft board images", accept_multiple_files=True)

translate_dct = {ord(c): '' for c in "_().:;"}

def convert_image(file):
    gray = np.asarray(Image.open(file).convert('L'))
    # We will eventually reverse the colors if dark mode
    dark_mode = (gray.mean() < 100)
    if dark_mode:
        thresh = 55
    else:
        thresh = 200
    # convert to black and white
    bw = np.asarray(gray).copy()
    bw[bw < thresh] = 0
    bw[bw >= thresh] = 255
    if dark_mode:
        bw = 255 - bw
    # Which rows contain only white pixels?
    rows = np.nonzero(bw.min(axis=1) == 255)[0]
    # Where are the gaps?  (Non-consecutive rows of white spaces.)
    gaps = np.nonzero(rows[1:] != rows[:-1] + 1)[0]
    data = []
    for draft_round in range(1,7):
        # what index in the `gaps` array corresponds to that round?
        slot = 6 - draft_round + 1
        # We are avoiding any all-white rows of pixels
        start = rows[gaps[-slot]]+1
        stop = rows[gaps[-slot]+1]
        height = stop - start
        # The division parts were found by trial and error
        # The +6 is to capture some y characters, originally misread as v
        imfile = Image.fromarray(bw[start+(height//4):stop-(height//3)+6, :])
        imfile.save("br_temp.png")
        reader = easyocr.Reader(['en'])
        result = reader.readtext("br_temp.png", paragraph=True)
        # the `sorted` is to get the names in the right order
        rd = []
        for (bbox, text) in sorted(result, key = lambda x: x[0][0][0]):
            text = text.translate(translate_dct)
            # Want to avoid round numbers being detected, depends on image size
            if len(text) < 5:
                continue
            rd.append(text)
        data.append(rd)
    return pd.DataFrame(data)

@st.fragment
def fragment_function():
    st.download_button("Download results as csv", data_as_csv, mime="text/csv")

if path:
    n = len(path)
    df_list = []
    for i, file in enumerate(path):
        st.write(f"Processing file {i+1} of {n}")
        df = convert_image(file)
        df.columns = df.columns + 1
        df["round"] = range(1, len(df)+1)
        df["draft num"] = i+1
        df_list.append(df)
    st.write("Finished")


    df_all = pd.concat(df_list, axis=0)
    data_as_csv= df_all.to_csv(index=False).encode("utf-8")

    st.dataframe(df_all)

    fragment_function()
    