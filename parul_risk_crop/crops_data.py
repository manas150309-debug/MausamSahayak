"""Crop requirement table for the rule-based advisor (version 1).

Each range is (min, optimum_low, optimum_high, max):
  temp_c   = mean air temperature during the growing season (deg C)
  rain_mm  = seasonal rainfall (mm)
  soil     = (min, best, max) soil moisture % at sowing (optional input)

!! These are APPROXIMATE textbook ranges, meant as starting values. They MUST be
!! reviewed by a local KVK / agriculture officer (Anil owns that step) and edited
!! for your district before you claim any recommendation accuracy.
"""

CROPS = [
    # ---- kharif (sowing ~Jun-Sep)
    dict(id="rice", en="Rice (paddy)", hi="धान (चावल)", seasons=["kharif"], temp=(20, 24, 30, 35), rain=(500, 900, 1800, 2800), soil=(40, 60, 90)),
    dict(id="maize", en="Maize", hi="मक्का", seasons=["kharif", "rabi", "zaid"], temp=(18, 21, 30, 35), rain=(300, 500, 900, 1500), soil=(30, 45, 75)),
    dict(id="bajra", en="Pearl millet (bajra)", hi="बाजरा", seasons=["kharif"], temp=(22, 25, 35, 42), rain=(200, 300, 600, 900), soil=(15, 25, 55)),
    dict(id="jowar", en="Sorghum (jowar)", hi="ज्वार", seasons=["kharif", "rabi"], temp=(20, 26, 32, 40), rain=(250, 400, 800, 1200), soil=(20, 30, 60)),
    dict(id="cotton", en="Cotton", hi="कपास", seasons=["kharif"], temp=(20, 24, 33, 40), rain=(400, 600, 1000, 1500), soil=(25, 40, 70)),
    dict(id="soybean", en="Soybean", hi="सोयाबीन", seasons=["kharif"], temp=(20, 22, 30, 35), rain=(400, 600, 1000, 1500), soil=(30, 45, 75)),
    dict(id="groundnut", en="Groundnut", hi="मूंगफली", seasons=["kharif"], temp=(20, 25, 30, 36), rain=(300, 500, 900, 1300), soil=(20, 35, 65)),
    dict(id="arhar", en="Pigeon pea (arhar/tur)", hi="अरहर (तुअर)", seasons=["kharif"], temp=(18, 20, 30, 38), rain=(400, 600, 1000, 1500), soil=(25, 40, 70)),
    dict(id="moong", en="Green gram (moong)", hi="मूंग", seasons=["kharif", "zaid"], temp=(22, 25, 35, 40), rain=(250, 350, 600, 900), soil=(20, 35, 65)),
    dict(id="sugarcane", en="Sugarcane", hi="गन्ना", seasons=["zaid", "kharif"], temp=(20, 25, 35, 40), rain=(750, 1100, 1800, 2500), soil=(40, 55, 85)),
    # ---- rabi (sowing ~Oct-Jan)
    dict(id="wheat", en="Wheat", hi="गेहूं", seasons=["rabi"], temp=(5, 10, 22, 30), rain=(40, 120, 400, 700), soil=(30, 45, 75)),
    dict(id="mustard", en="Mustard (sarson)", hi="सरसों", seasons=["rabi"], temp=(5, 10, 25, 32), rain=(25, 60, 300, 500), soil=(20, 35, 65)),
    dict(id="chickpea", en="Chickpea (chana)", hi="चना", seasons=["rabi"], temp=(8, 15, 25, 32), rain=(30, 80, 300, 500), soil=(20, 30, 60)),
    dict(id="barley", en="Barley (jau)", hi="जौ", seasons=["rabi"], temp=(5, 10, 22, 30), rain=(30, 80, 300, 500), soil=(20, 35, 65)),
    dict(id="potato", en="Potato", hi="आलू", seasons=["rabi"], temp=(8, 12, 20, 26), rain=(50, 150, 400, 600), soil=(35, 50, 75)),
    dict(id="peas", en="Field pea (matar)", hi="मटर", seasons=["rabi"], temp=(7, 10, 18, 24), rain=(60, 150, 400, 600), soil=(30, 45, 70)),
    # ---- zaid (sowing ~Feb-May)
    dict(id="watermelon", en="Watermelon", hi="तरबूज", seasons=["zaid"], temp=(20, 25, 35, 42), rain=(30, 50, 200, 400), soil=(20, 30, 60)),
    dict(id="cucumber", en="Cucumber", hi="खीरा", seasons=["zaid"], temp=(18, 22, 32, 38), rain=(30, 60, 250, 450), soil=(30, 45, 70)),
    dict(id="okra", en="Okra (bhindi)", hi="भिंडी", seasons=["zaid", "kharif"], temp=(20, 24, 35, 40), rain=(100, 300, 800, 1200), soil=(30, 40, 70)),
    dict(id="sunflower", en="Sunflower", hi="सूरजमुखी", seasons=["zaid"], temp=(15, 20, 30, 36), rain=(100, 300, 600, 900), soil=(25, 35, 65)),
]
CROPS_BY_ID = {c["id"]: c for c in CROPS}
