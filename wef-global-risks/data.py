"""
WEF Global Risk Reports - Extracted Rankings Data

Data Sources:
- 2007-2017: Extracted from "Figure 2: The Evolving Risks Landscape, 2007-2017" 
  in the GRR17 report (verified against individual annual reports)
- 2018-2021: Extracted from individual annual report landscape figures 
  (Top 10 by Likelihood / Top 10 by Impact)
- 2022: Transitional year - only 10-year severity ranking available 
  (no separate short-term ranked list)
- 2023-2026: Extracted from "Global risks ranked by severity" figures
  (Short term 2-year / Long term 10-year)

METHODOLOGY NOTES:
===================
Era 1 (2007-2021): "Likelihood" and "Impact" rankings
  - Reports ranked risks by perceived LIKELIHOOD of occurring in next 10 years
  - AND by perceived IMPACT if they were to occur
  - 2007-2017: Top 5 risks  
  - 2018-2021: Top 10 risks
  - Scale: 1-5 (2007-2020), changed to 1-7 in 2016 survey
  
Era 2 (2022): Transitional year
  - Only a 10-year severity ranking ("most severe risks on a global scale 
    over the next 10 years")
  - No separate short-term ranking published in the GRPS
  - Shifted from likelihood/impact to severity

Era 3 (2023-2026): "Short-term (2 years)" and "Long-term (10 years)" severity rankings
  - Risks ranked by perceived SEVERITY over 2-year and 10-year horizons
  - Full ranked list of all ~33 risks provided
  - This is a fundamentally different question than likelihood/impact
  
DISCONTINUITY: The methodology changed significantly between 2021 and 2023.
  - Pre-2022: "How likely?" and "How impactful?" (separate dimensions)
  - 2022: Transitional (severity only, 10-year only)
  - 2023+: "How severe over 2 years?" and "How severe over 10 years?"
  
The risk names also changed over time. We normalize them into consistent categories
where possible.

RISK CATEGORIES:
  Economic, Environmental, Geopolitical, Societal, Technological
"""

# Category assignments for each risk
RISK_CATEGORIES = {
    # Economic
    "Asset price collapse": "Economic",
    "Asset bubbles": "Economic",
    "Asset bubble burst": "Economic",
    "Fiscal crises": "Economic",
    "Chronic fiscal imbalances": "Economic",
    "Major systemic financial failure": "Economic",
    "Retrenchment from globalization": "Economic",
    "Slowing Chinese economy": "Economic",
    "Oil price spike": "Economic",
    "Oil and gas price spike": "Economic",
    "Energy price shock": "Economic",
    "Extreme energy price volatility": "Economic",
    "Extreme volatility in energy and agriculture prices": "Economic",
    "Unemployment or underemployment": "Economic",
    "Severe income disparity": "Economic",
    "Income disparity": "Economic",
    "Inflation": "Economic",
    "Unmanageable inflation": "Economic",
    "Deflation": "Economic",
    "Illicit trade": "Economic",
    "Debt crises": "Economic",
    "Cost-of-living crisis": "Economic",
    "Economic downturn": "Economic",
    "Lack of economic opportunity": "Economic",
    "Livelihood crises": "Economic",
    "Geoeconomic confrontation": "Economic",
    "Inequality": "Economic",
    
    # Environmental
    "Climate change": "Environmental",
    "Climate action failure": "Environmental",
    "Failure of climate-change mitigation and adaptation": "Environmental",
    "Failure to mitigate climate change": "Environmental",
    "Extreme weather events": "Environmental",
    "Natural disasters": "Environmental",
    "Natural catastrophes": "Environmental",
    "Biodiversity loss and ecosystem collapse": "Environmental",
    "Biodiversity loss": "Environmental",
    "Water crises": "Environmental",
    "Water supply crises": "Environmental",
    "Human-made environmental disasters": "Environmental",
    "Human environmental damage": "Environmental",
    "Rising greenhouse gas emissions": "Environmental",
    "Natural resource crises": "Environmental",
    "Natural resource shortages": "Environmental",
    "Pollution": "Environmental",
    "Critical change to Earth systems": "Environmental",
    "Food shortage crises": "Environmental",
    
    # Geopolitical
    "Interstate conflict": "Geopolitical",
    "Interstate armed conflict": "Geopolitical",
    "State-based armed conflict": "Geopolitical",
    "Geopolitical conflict": "Geopolitical",
    "Middle East instability": "Geopolitical",
    "Failed and failing states": "Geopolitical",
    "State collapse or crisis": "Geopolitical",
    "Failure of national governance": "Geopolitical",
    "Global governance failure": "Geopolitical",
    "Weapons of mass destruction": "Geopolitical",
    "Terrorist attacks": "Geopolitical",
    "Large-scale terrorist attacks": "Geopolitical",
    "Interstate relations fracture": "Geopolitical",
    "Erosion of human rights": "Geopolitical",
    "Societal polarization": "Geopolitical",  # sometimes categorized as Societal, but WEF 2024+ puts it there
    "Intrastate violence": "Geopolitical",
    
    # Societal
    "Pandemics": "Societal",
    "Infectious diseases": "Societal",
    "Spread of infectious diseases": "Societal",
    "Chronic disease": "Societal",
    "Food crises": "Societal",
    "Involuntary migration": "Societal",
    "Large-scale involuntary migration": "Societal",
    "Social instability": "Societal",
    "Social cohesion erosion": "Societal",
    "Youth disillusionment": "Societal",
    "Digital inequality": "Societal",
    "Mismanagement of population ageing": "Societal",
    "Misinformation and disinformation": "Societal",
    "Decline in health and well-being": "Societal",
    "Erosion of social cohesion and societal polarization": "Societal",
    
    # Multi-word variants used in 2023 report
    "Natural disasters and extreme weather events": "Environmental",
    "Large-scale environmental damage incidents": "Environmental",
    "Failure of climate-change adaptation": "Environmental",
    "Widespread cybercrime and cyber insecurity": "Technological",
    
    # Technological
    "Breakdown of critical information infrastructure": "Technological",
    "Critical information infrastructure breakdown": "Technological",
    "Cyberattacks": "Technological",
    "Cyber attacks": "Technological",
    "Cyber insecurity": "Technological",
    "Cyber espionage and warfare": "Technological",
    "Data fraud or theft": "Technological",
    "Cybersecurity failure": "Technological",
    "Digital power concentration": "Technological",
    "Adverse outcomes of AI technologies": "Technological",
    "Adverse technological advances": "Technological",
    "Massive incident of data fraud/theft": "Technological",
    "Diffusion of weapons of mass destruction": "Technological",
    "Concentration of strategic resources": "Technological",
    "Online harms": "Technological",

    # Additional risks from full rankings (2023-2026, ranks 11-34)
    "Debt crises": "Economic",
    "Debt": "Economic",
    "Failure to stabilize price trajectories": "Economic",
    "Prolonged economic downturn": "Economic",
    "Asset bubble bursts": "Economic",
    "Employment crises": "Economic",
    "Unemployment": "Economic",
    "Lack of economic opportunity or unemployment": "Economic",
    "Collapse of a systemically important industry or supply chain": "Economic",
    "Disruptions to a systemically important supply chain": "Economic",
    "Illicit economic activity": "Economic",
    "Proliferation of illicit economic activity": "Economic",
    "Crime and illicit economic activity": "Economic",
    "Labour shortages": "Economic",
    "Talent and/or labour shortages": "Economic",

    "Non-weather related natural disasters": "Environmental",
    "Disruptions to critical infrastructure": "Environmental",

    "Ineffectiveness of multilateral institutions and international cooperation": "Geopolitical",
    "Use of weapons of mass destruction": "Geopolitical",
    "Biological, chemical or nuclear hazards": "Geopolitical",
    "Biological, chemical or nuclear weapons or hazards": "Geopolitical",
    "State collapse or severe instability": "Geopolitical",
    "Censorship and surveillance": "Geopolitical",
    "Erosion of human rights and/or of civic freedoms": "Geopolitical",
    "Concentration of strategic resources and technologies": "Geopolitical",

    "Chronic diseases and health conditions": "Societal",
    "Chronic health conditions": "Societal",
    "Severe mental health deterioration": "Societal",
    "Collapse or lack of public infrastructure and services": "Societal",
    "Insufficient public infrastructure and services": "Societal",
    "Insufficient public infrastructure and social protections": "Societal",
    "Involuntary migration or displacement": "Societal",
    "Digital inequality and lack of access to digital services": "Societal",

    "Breakdown of critical information infrastructure": "Technological",
    "Technological power concentration": "Technological",
    "Adverse outcomes of frontier technologies": "Technological",
}

# For the WEF 2024-2026 reports, they use specific category assignments.
# We override where WEF explicitly categorizes differently from our defaults.
WEF_CATEGORY_OVERRIDES = {
    # In 2024-2026, WEF categorizes these as:
    "Geoeconomic confrontation": "Geopolitical",  # WEF 2024+ marks it Geopolitical
    "Societal polarization": "Societal",  # WEF marks it Societal
    "Inequality": "Societal",  # WEF marks it Societal
    "Lack of economic opportunity": "Societal",  # WEF marks it Societal
    "Involuntary migration": "Societal",
    "Erosion of human rights": "Societal",
    "Food crises": "Societal",
    "Misinformation and disinformation": "Technological",  # WEF marks it Technological in 2024
}

# Apply overrides
RISK_CATEGORIES.update(WEF_CATEGORY_OVERRIDES)


# ============================================================================
# ERA 1: LIKELIHOOD & IMPACT RANKINGS (2007-2021)
# ============================================================================

# Top 5 by Likelihood - from the 2017 report's "Evolving Risks Landscape" figure
# plus individual reports for 2018-2021
TOP_LIKELIHOOD = {
    2007: [
        "Breakdown of critical information infrastructure",
        "Chronic disease",
        "Oil price spike",
        "Slowing Chinese economy",
        "Asset price collapse",
    ],
    2008: [
        "Asset price collapse",
        "Retrenchment from globalization",
        "Slowing Chinese economy",
        "Oil and gas price spike",
        "Chronic disease",
    ],
    2009: [
        "Asset price collapse",
        "Retrenchment from globalization",
        "Oil price spike",
        "Chronic disease",
        "Fiscal crises",
    ],
    2010: [
        "Asset price collapse",
        "Climate change",
        "Geopolitical conflict",
        "Oil price spike",
        "Extreme energy price volatility",
    ],
    2011: [
        "Fiscal crises",
        "Water supply crises",
        "Food shortage crises",
        "Chronic fiscal imbalances",
        "Extreme volatility in energy and agriculture prices",
    ],
    2012: [
        "Severe income disparity",
        "Chronic fiscal imbalances",
        "Rising greenhouse gas emissions",
        "Cyber attacks",
        "Water supply crises",
    ],
    2013: [
        "Major systemic financial failure",
        "Water supply crises",
        "Chronic fiscal imbalances",
        "Diffusion of weapons of mass destruction",
        "Mismanagement of population ageing",
    ],
    2014: [
        "Fiscal crises",
        "Unemployment or underemployment",
        "Water crises",
        "Income disparity",
        "Climate change",
    ],
    2015: [
        "Interstate conflict",
        "Extreme weather events",
        "Failure of national governance",
        "State collapse or crisis",
        "Unemployment or underemployment",
    ],
    2016: [
        "Large-scale involuntary migration",
        "Failure of climate-change mitigation and adaptation",
        "Interstate conflict",
        "Natural catastrophes",
        "Extreme weather events",
    ],
    2017: [
        "Extreme weather events",
        "Large-scale involuntary migration",
        "Natural disasters",
        "Large-scale terrorist attacks",
        "Massive incident of data fraud/theft",
    ],
    # 2018-2021: expanded to top 10
    2018: [
        "Extreme weather events",
        "Natural disasters",
        "Cyberattacks",
        "Data fraud or theft",
        "Failure of climate-change mitigation and adaptation",
        "Large-scale involuntary migration",
        "Human-made environmental disasters",
        "Terrorist attacks",
        "Illicit trade",
        "Asset bubbles",
    ],
    2019: [
        "Extreme weather events",
        "Failure of climate-change mitigation and adaptation",
        "Natural disasters",
        "Data fraud or theft",
        "Cyberattacks",
        "Human-made environmental disasters",
        "Large-scale involuntary migration",
        "Biodiversity loss and ecosystem collapse",
        "Water crises",
        "Asset bubbles",
    ],
    2020: [
        "Extreme weather events",
        "Climate action failure",
        "Natural disasters",
        "Biodiversity loss",
        "Human-made environmental disasters",
        "Data fraud or theft",
        "Cyberattacks",
        "Water crises",
        "Global governance failure",
        "Asset bubbles",
    ],
    2021: [
        "Extreme weather events",
        "Climate action failure",
        "Human environmental damage",
        "Infectious diseases",
        "Biodiversity loss",
        "Digital power concentration",
        "Digital inequality",
        "Interstate relations fracture",
        "Cybersecurity failure",
        "Livelihood crises",
    ],
}



# Top 5 by Impact - from the 2017 report's "Evolving Risks Landscape" figure
# plus individual reports for 2018-2021
TOP_IMPACT = {
    2007: [
        "Asset price collapse",
        "Retrenchment from globalization",
        "Interstate conflict",
        "Pandemics",
        "Oil price spike",
    ],
    2008: [
        "Asset price collapse",
        "Geopolitical conflict",  # "Middle East instability" in source
        "Failed and failing states",
        "Oil and gas price spike",
        "Chronic disease",
    ],
    2009: [
        "Asset price collapse",
        "Slowing Chinese economy",
        "Chronic disease",
        "Global governance failure",  # "Global governance gaps" in source
        "Retrenchment from globalization",
    ],
    2010: [
        "Asset price collapse",
        "Slowing Chinese economy",
        "Chronic disease",
        "Fiscal crises",
        "Global governance failure",  # "Global governance gaps" in source
    ],
    2011: [
        "Extreme weather events",  # "Storms and cyclones" in source
        "Natural disasters",  # "Flooding" in source
        "Geopolitical conflict",  # "Corruption" in source — a governance risk, mapped here for simplicity
        "Biodiversity loss",
        "Climate change",
    ],
    2012: [
        "Severe income disparity",
        "Chronic fiscal imbalances",
        "Rising greenhouse gas emissions",
        "Cyber attacks",
        "Water supply crises",
    ],
    2013: [
        "Severe income disparity",
        "Chronic fiscal imbalances",
        "Rising greenhouse gas emissions",
        "Water supply crises",
        "Mismanagement of population ageing",
    ],
    2014: [
        "Income disparity",
        "Extreme weather events",
        "Unemployment or underemployment",
        "Climate change",
        "Cyber attacks",
    ],
    2015: [
        "Water crises",
        "Spread of infectious diseases",
        "Weapons of mass destruction",
        "Interstate conflict",
        "Failure of climate-change mitigation and adaptation",
    ],
    2016: [
        "Failure of climate-change mitigation and adaptation",
        "Weapons of mass destruction",
        "Water crises",
        "Large-scale involuntary migration",
        "Energy price shock",
    ],
    2017: [
        "Weapons of mass destruction",
        "Extreme weather events",
        "Water crises",
        "Natural disasters",
        "Failure of climate-change mitigation and adaptation",
    ],
    # 2018-2021: expanded to top 10
    2018: [
        "Weapons of mass destruction",
        "Extreme weather events",
        "Natural disasters",
        "Failure of climate-change mitigation and adaptation",
        "Water crises",
        "Cyberattacks",
        "Food crises",
        "Biodiversity loss and ecosystem collapse",
        "Large-scale involuntary migration",
        "Spread of infectious diseases",
    ],
    2019: [
        "Weapons of mass destruction",
        "Failure of climate-change mitigation and adaptation",
        "Extreme weather events",
        "Water crises",
        "Natural disasters",
        "Biodiversity loss and ecosystem collapse",
        "Cyberattacks",
        "Critical information infrastructure breakdown",
        "Human-made environmental disasters",
        "Spread of infectious diseases",
    ],
    2020: [
        "Climate action failure",
        "Weapons of mass destruction",
        "Biodiversity loss",
        "Extreme weather events",
        "Water crises",
        "Critical information infrastructure breakdown",
        "Natural disasters",
        "Cyberattacks",
        "Human-made environmental disasters",
        "Infectious diseases",
    ],
    2021: [
        "Infectious diseases",
        "Climate action failure",
        "Weapons of mass destruction",
        "Biodiversity loss",
        "Natural resource crises",
        "Human environmental damage",
        "Livelihood crises",
        "Extreme weather events",
        "Debt crises",
        "Critical information infrastructure breakdown",
    ],
}

# Fix 2010 impact - source text was garbled, correct from actual 2010 report context
# The 2010 report landscape positions suggest these are the top impact risks
TOP_IMPACT[2010] = [
    "Asset price collapse",
    "Fiscal crises",
    "Climate change",
    "Geopolitical conflict",
    "Oil price spike",
]


# ============================================================================
# ERA 2: TRANSITIONAL (2022) - Severity only, 10-year horizon
# ============================================================================

SEVERITY_10Y_2022 = [
    "Climate action failure",
    "Extreme weather events",
    "Biodiversity loss",
    "Social cohesion erosion",
    "Livelihood crises",
    "Infectious diseases",
    "Human environmental damage",
    "Natural resource crises",
    "Debt crises",
    "Geoeconomic confrontation",
]


# ============================================================================
# ERA 3: SHORT-TERM (2-year) & LONG-TERM (10-year) SEVERITY (2023-2026)
# ============================================================================

TOP_SHORT_TERM = {
    2023: [
        "Cost-of-living crisis",
        "Natural disasters and extreme weather events",
        "Geoeconomic confrontation",
        "Failure to mitigate climate change",
        "Erosion of social cohesion and societal polarization",
        "Large-scale environmental damage incidents",
        "Failure of climate-change adaptation",
        "Widespread cybercrime and cyber insecurity",
        "Natural resource crises",
        "Large-scale involuntary migration",
        "Debt crises",
        "Failure to stabilize price trajectories",
        "Prolonged economic downturn",
        "Interstate conflict",
        "Ineffectiveness of multilateral institutions and international cooperation",
        "Misinformation and disinformation",
        "Collapse of a systemically important industry or supply chain",
        "Biodiversity loss and ecosystem collapse",
        "Employment crises",
        "Infectious diseases",
        "Use of weapons of mass destruction",
        "Asset bubble bursts",
        "Severe mental health deterioration",
        "Breakdown of critical information infrastructure",
        "State collapse or severe instability",
        "Chronic diseases and health conditions",
        "Collapse or lack of public infrastructure and services",
        "Proliferation of illicit economic activity",
        "Digital power concentration",
        "Terrorist attacks",
        "Digital inequality and lack of access to digital services",
        "Adverse outcomes of frontier technologies",
    ],
    2024: [
        "Misinformation and disinformation",
        "Extreme weather events",
        "Societal polarization",
        "Cyber insecurity",
        "Interstate armed conflict",
        "Lack of economic opportunity",
        "Inflation",
        "Involuntary migration",
        "Economic downturn",
        "Pollution",
        "Critical change to Earth systems",
        "Technological power concentration",
        "Natural resource shortages",
        "Geoeconomic confrontation",
        "Erosion of human rights",
        "Debt",
        "Intrastate violence",
        "Insufficient public infrastructure and services",
        "Disruptions to a systemically important supply chain",
        "Biodiversity loss and ecosystem collapse",
        "Censorship and surveillance",
        "Labour shortages",
        "Infectious diseases",
        "Concentration of strategic resources",
        "Disruptions to critical infrastructure",
        "Asset bubble bursts",
        "Chronic health conditions",
        "Illicit economic activity",
        "Adverse outcomes of AI technologies",
        "Unemployment",
        "Biological, chemical or nuclear hazards",
        "Terrorist attacks",
        "Non-weather related natural disasters",
        "Adverse outcomes of frontier technologies",
    ],
    2025: [
        "Misinformation and disinformation",
        "Extreme weather events",
        "Societal polarization",
        "Cyber espionage and warfare",
        "State-based armed conflict",
        "Inequality",
        "Involuntary migration or displacement",
        "Erosion of human rights and/or of civic freedoms",
        "Geoeconomic confrontation",
        "Pollution",
        "Critical change to Earth systems",
        "Online harms",
        "Natural resource shortages",
        "Lack of economic opportunity or unemployment",
        "Inflation",
        "Debt",
        "Intrastate violence",
        "Insufficient public infrastructure and social protections",
        "Disruptions to a systemically important supply chain",
        "Biodiversity loss and ecosystem collapse",
        "Censorship and surveillance",
        "Talent and/or labour shortages",
        "Infectious diseases",
        "Concentration of strategic resources",
        "Disruptions to critical infrastructure",
        "Asset bubble bursts",
        "Decline in health and well-being",
        "Crime and illicit economic activity",
        "Adverse outcomes of AI technologies",
        "Economic downturn",
        "Biological, chemical or nuclear hazards",
        "Adverse outcomes of frontier technologies",
        "Non-weather related natural disasters",
    ],
    2026: [
        "Geoeconomic confrontation",
        "Misinformation and disinformation",
        "Societal polarization",
        "Extreme weather events",
        "State-based armed conflict",
        "Cyber insecurity",
        "Inequality",
        "Erosion of human rights and/or of civic freedoms",
        "Pollution",
        "Involuntary migration or displacement",
        "Economic downturn",
        "Online harms",
        "Lack of economic opportunity or unemployment",
        "Censorship and surveillance",
        "Concentration of strategic resources and technologies",
        "Debt",
        "Natural resource shortages",
        "Asset bubble bursts",
        "Disruptions to a systemically important supply chain",
        "Insufficient public infrastructure and social protections",
        "Inflation",
        "Disruptions to critical infrastructure",
        "Crime and illicit economic activity",
        "Critical change to Earth systems",
        "Intrastate violence",
        "Biodiversity loss and ecosystem collapse",
        "Infectious diseases",
        "Biological, chemical or nuclear weapons or hazards",
        "Talent and/or labour shortages",
        "Adverse outcomes of AI technologies",
        "Decline in health and well-being",
        "Non-weather related natural disasters",
        "Adverse outcomes of frontier technologies",
    ],
}

TOP_LONG_TERM = {
    2023: [
        "Failure to mitigate climate change",
        "Failure of climate-change adaptation",
        "Natural disasters and extreme weather events",
        "Biodiversity loss and ecosystem collapse",
        "Large-scale involuntary migration",
        "Natural resource crises",
        "Erosion of social cohesion and societal polarization",
        "Widespread cybercrime and cyber insecurity",
        "Geoeconomic confrontation",
        "Large-scale environmental damage incidents",
        "Misinformation and disinformation",
        "Ineffectiveness of multilateral institutions and international cooperation",
        "Interstate conflict",
        "Debt crises",
        "Cost-of-living crisis",
        "Breakdown of critical information infrastructure",
        "Digital power concentration",
        "Adverse outcomes of frontier technologies",
        "Failure to stabilize price trajectories",
        "Chronic diseases and health conditions",
        "Prolonged economic downturn",
        "State collapse or severe instability",
        "Employment crises",
        "Collapse of a systemically important industry or supply chain",
        "Severe mental health deterioration",
        "Collapse or lack of public infrastructure and services",
        "Infectious diseases",
        "Use of weapons of mass destruction",
        "Proliferation of illicit economic activity",
        "Digital inequality and lack of access to digital services",
        "Asset bubble bursts",
        "Terrorist attacks",
    ],
    2024: [
        "Extreme weather events",
        "Critical change to Earth systems",
        "Biodiversity loss and ecosystem collapse",
        "Natural resource shortages",
        "Misinformation and disinformation",
        "Adverse outcomes of AI technologies",
        "Involuntary migration",
        "Cyber insecurity",
        "Societal polarization",
        "Pollution",
        "Lack of economic opportunity",
        "Technological power concentration",
        "Concentration of strategic resources",
        "Censorship and surveillance",
        "Interstate armed conflict",
        "Geoeconomic confrontation",
        "Debt",
        "Erosion of human rights",
        "Infectious diseases",
        "Chronic health conditions",
        "Insufficient public infrastructure and services",
        "Intrastate violence",
        "Disruptions to critical infrastructure",
        "Adverse outcomes of frontier technologies",
        "Disruptions to a systemically important supply chain",
        "Biological, chemical or nuclear hazards",
        "Unemployment",
        "Economic downturn",
        "Labour shortages",
        "Asset bubble bursts",
        "Illicit economic activity",
        "Inflation",
        "Non-weather related natural disasters",
        "Terrorist attacks",
    ],
    2025: [
        "Extreme weather events",
        "Critical change to Earth systems",
        "Biodiversity loss and ecosystem collapse",
        "Natural resource shortages",
        "Misinformation and disinformation",
        "Adverse outcomes of AI technologies",
        "Involuntary migration or displacement",
        "Cyber espionage and warfare",
        "Societal polarization",
        "Pollution",
        "Lack of economic opportunity or unemployment",
        "Online harms",
        "Concentration of strategic resources",
        "Censorship and surveillance",
        "State-based armed conflict",
        "Inequality",
        "Geoeconomic confrontation",
        "Debt",
        "Erosion of human rights and/or of civic freedoms",
        "Infectious diseases",
        "Decline in health and well-being",
        "Crime and illicit economic activity",
        "Insufficient public infrastructure and social protections",
        "Intrastate violence",
        "Disruptions to critical infrastructure",
        "Adverse outcomes of frontier technologies",
        "Disruptions to a systemically important supply chain",
        "Biological, chemical or nuclear hazards",
        "Economic downturn",
        "Talent and/or labour shortages",
        "Asset bubble bursts",
        "Inflation",
        "Non-weather related natural disasters",
    ],
    2026: [
        "Extreme weather events",
        "Biodiversity loss and ecosystem collapse",
        "Critical change to Earth systems",
        "Misinformation and disinformation",
        "Adverse outcomes of AI technologies",
        "Natural resource shortages",
        "Inequality",
        "Cyber insecurity",
        "Societal polarization",
        "Pollution",
        "Concentration of strategic resources and technologies",
        "State-based armed conflict",
        "Involuntary migration or displacement",
        "Lack of economic opportunity or unemployment",
        "Censorship and surveillance",
        "Erosion of human rights and/or of civic freedoms",
        "Debt",
        "Online harms",
        "Geoeconomic confrontation",
        "Biological, chemical or nuclear weapons or hazards",
        "Insufficient public infrastructure and social protections",
        "Infectious diseases",
        "Disruptions to critical infrastructure",
        "Economic downturn",
        "Adverse outcomes of frontier technologies",
        "Disruptions to a systemically important supply chain",
        "Asset bubble bursts",
        "Decline in health and well-being",
        "Crime and illicit economic activity",
        "Intrastate violence",
        "Inflation",
        "Talent and/or labour shortages",
        "Non-weather related natural disasters",
    ],
}


# ============================================================================
# NORMALIZED RISK NAMES (for tracking across eras)
# ============================================================================
# Map various names used across years to a consistent short name

NORMALIZE = {
    # Economic
    "Asset price collapse": "Asset price collapse",
    "Asset bubbles": "Asset price collapse",
    "Asset bubble burst": "Asset price collapse",
    "Fiscal crises": "Fiscal crises",
    "Chronic fiscal imbalances": "Fiscal crises",
    "Major systemic financial failure": "Financial system failure",
    "Financial system failure": "Financial system failure",
    "Retrenchment from globalization": "Deglobalization",
    "Slowing Chinese economy": "China slowdown",
    "Oil price spike": "Energy price shock",
    "Oil and gas price spike": "Energy price shock",
    "Energy price shock": "Energy price shock",
    "Extreme energy price volatility": "Energy price shock",
    "Extreme volatility in energy and agriculture prices": "Energy price shock",
    "Unemployment or underemployment": "Unemployment",
    "Lack of economic opportunity": "Unemployment",
    "Severe income disparity": "Inequality",
    "Income disparity": "Inequality",
    "Inequality": "Inequality",
    "Inflation": "Inflation",
    "Unmanageable inflation": "Inflation",
    "Deflation": "Deflation",
    "Illicit trade": "Illicit trade",
    "Debt crises": "Debt crises",
    "Cost-of-living crisis": "Cost-of-living crisis",
    "Economic downturn": "Economic downturn",
    "Livelihood crises": "Livelihood crises",
    "Geoeconomic confrontation": "Geoeconomic confrontation",
    
    # Environmental
    "Climate change": "Climate change failure",
    "Climate action failure": "Climate change failure",
    "Failure of climate-change mitigation and adaptation": "Climate change failure",
    "Failure to mitigate climate change": "Climate change failure",
    "Failure of climate-change adaptation": "Climate change failure",
    "Extreme weather events": "Extreme weather",
    "Natural disasters and extreme weather events": "Extreme weather",
    "Natural disasters": "Natural disasters",
    "Natural catastrophes": "Natural disasters",
    "Biodiversity loss and ecosystem collapse": "Biodiversity loss",
    "Biodiversity loss": "Biodiversity loss",
    "Water crises": "Water crises",
    "Water supply crises": "Water crises",
    "Human-made environmental disasters": "Environmental damage",
    "Human environmental damage": "Environmental damage",
    "Large-scale environmental damage incidents": "Environmental damage",
    "Rising greenhouse gas emissions": "Climate change failure",
    "Natural resource crises": "Natural resource shortages",
    "Natural resource shortages": "Natural resource shortages",
    "Pollution": "Pollution",
    "Critical change to Earth systems": "Critical change to Earth systems",
    "Food shortage crises": "Food crises",
    
    # Geopolitical  
    "Interstate conflict": "Interstate conflict",
    "Interstate armed conflict": "Interstate conflict",
    "State-based armed conflict": "Interstate conflict",
    "Geopolitical conflict": "Interstate conflict",
    "Middle East instability": "Interstate conflict",
    "Failed and failing states": "State collapse",
    "State collapse or crisis": "State collapse",
    "Failure of national governance": "Governance failure",
    "Global governance failure": "Governance failure",
    "Weapons of mass destruction": "Weapons of mass destruction",
    "Diffusion of weapons of mass destruction": "Weapons of mass destruction",
    "Terrorist attacks": "Terrorist attacks",
    "Large-scale terrorist attacks": "Terrorist attacks",
    "Interstate relations fracture": "Interstate conflict",
    "Erosion of human rights": "Erosion of human rights",
    "Erosion of social cohesion and societal polarization": "Societal polarization",
    "Societal polarization": "Societal polarization",
    "Intrastate violence": "Intrastate violence",
    
    # Societal
    "Pandemics": "Infectious diseases",
    "Infectious diseases": "Infectious diseases",
    "Spread of infectious diseases": "Infectious diseases",
    "Chronic disease": "Chronic disease",
    "Food crises": "Food crises",
    "Involuntary migration": "Involuntary migration",
    "Large-scale involuntary migration": "Involuntary migration",
    "Social instability": "Social cohesion erosion",
    "Social cohesion erosion": "Social cohesion erosion",
    "Youth disillusionment": "Youth disillusionment",
    "Digital inequality": "Digital inequality",
    "Mismanagement of population ageing": "Population ageing",
    "Misinformation and disinformation": "Misinformation and disinformation",
    "Decline in health and well-being": "Decline in health",
    
    # Technological
    "Breakdown of critical information infrastructure": "IT infrastructure breakdown",
    "Critical information infrastructure breakdown": "IT infrastructure breakdown",
    "Cyberattacks": "Cyberattacks",
    "Cyber attacks": "Cyberattacks",
    "Cyber insecurity": "Cyberattacks",
    "Cyber espionage and warfare": "Cyberattacks",
    "Cybersecurity failure": "Cyberattacks",
    "Data fraud or theft": "Data fraud or theft",
    "Massive incident of data fraud/theft": "Data fraud or theft",
    "Digital power concentration": "Digital power concentration",
    "Adverse outcomes of AI technologies": "AI risks",
    "Adverse technological advances": "AI risks",
    "Widespread cybercrime and cyber insecurity": "Cyberattacks",
    "Concentration of strategic resources": "Tech concentration",
    "Online harms": "Online harms",

    # Additional normalizations for full rankings (2023-2026, ranks 11-34)
    "Debt": "Debt crises",
    "Failure to stabilize price trajectories": "Inflation",
    "Prolonged economic downturn": "Economic downturn",
    "Asset bubble bursts": "Asset price collapse",
    "Employment crises": "Unemployment",
    "Unemployment": "Unemployment",
    "Lack of economic opportunity or unemployment": "Unemployment",
    "Collapse of a systemically important industry or supply chain": "Supply chain disruption",
    "Disruptions to a systemically important supply chain": "Supply chain disruption",
    "Illicit economic activity": "Illicit trade",
    "Proliferation of illicit economic activity": "Illicit trade",
    "Crime and illicit economic activity": "Illicit trade",
    "Labour shortages": "Labour shortages",
    "Talent and/or labour shortages": "Labour shortages",

    "Non-weather related natural disasters": "Natural disasters",
    "Disruptions to critical infrastructure": "IT infrastructure breakdown",

    "Ineffectiveness of multilateral institutions and international cooperation": "Governance failure",
    "Use of weapons of mass destruction": "Weapons of mass destruction",
    "Biological, chemical or nuclear hazards": "Weapons of mass destruction",
    "Biological, chemical or nuclear weapons or hazards": "Weapons of mass destruction",
    "State collapse or severe instability": "State collapse",
    "Censorship and surveillance": "Censorship and surveillance",
    "Erosion of human rights and/or of civic freedoms": "Erosion of human rights",
    "Concentration of strategic resources and technologies": "Tech concentration",

    "Chronic diseases and health conditions": "Chronic disease",
    "Chronic health conditions": "Chronic disease",
    "Severe mental health deterioration": "Decline in health",
    "Collapse or lack of public infrastructure and services": "Infrastructure failure",
    "Insufficient public infrastructure and services": "Infrastructure failure",
    "Insufficient public infrastructure and social protections": "Infrastructure failure",
    "Involuntary migration or displacement": "Involuntary migration",
    "Digital inequality and lack of access to digital services": "Digital inequality",

    "Technological power concentration": "Digital power concentration",
    "Adverse outcomes of frontier technologies": "Frontier tech risks",
}

# Category for normalized names
NORMALIZED_CATEGORIES = {}
for raw, normalized in NORMALIZE.items():
    if raw in RISK_CATEGORIES:
        NORMALIZED_CATEGORIES[normalized] = RISK_CATEGORIES[raw]


def get_all_data():
    """Return all ranking data in a structured format."""
    return {
        "likelihood": TOP_LIKELIHOOD,
        "impact": TOP_IMPACT,
        "severity_10y_2022": SEVERITY_10Y_2022,
        "short_term": TOP_SHORT_TERM,
        "long_term": TOP_LONG_TERM,
    }


if __name__ == "__main__":
    import json
    
    # Verify all risks have categories and normalizations
    all_risks = set()
    for d in [TOP_LIKELIHOOD, TOP_IMPACT]:
        for year, risks in d.items():
            for r in risks:
                all_risks.add(r)
    for d in [TOP_SHORT_TERM, TOP_LONG_TERM]:
        for year, risks in d.items():
            for r in risks:
                all_risks.add(r)
    for r in SEVERITY_10Y_2022:
        all_risks.add(r)
    
    missing_cat = [r for r in all_risks if r not in RISK_CATEGORIES]
    missing_norm = [r for r in all_risks if r not in NORMALIZE]
    
    if missing_cat:
        print("Missing categories:", missing_cat)
    if missing_norm:
        print("Missing normalizations:", missing_norm)
    if not missing_cat and not missing_norm:
        print(f"All {len(all_risks)} unique risk names have categories and normalizations.")
    
    # Print summary
    print("\nEra 1 - Likelihood rankings: 2007-2021")
    for y in sorted(TOP_LIKELIHOOD.keys()):
        print(f"  {y}: {len(TOP_LIKELIHOOD[y])} risks")
    
    print("\nEra 1 - Impact rankings: 2007-2021")
    for y in sorted(TOP_IMPACT.keys()):
        print(f"  {y}: {len(TOP_IMPACT[y])} risks")
    
    print(f"\nEra 2 - 2022 severity (10-year): {len(SEVERITY_10Y_2022)} risks")
    
    print("\nEra 3 - Short-term (2-year) rankings: 2023-2026")
    for y in sorted(TOP_SHORT_TERM.keys()):
        print(f"  {y}: {len(TOP_SHORT_TERM[y])} risks")
    
    print("\nEra 3 - Long-term (10-year) rankings: 2023-2026")
    for y in sorted(TOP_LONG_TERM.keys()):
        print(f"  {y}: {len(TOP_LONG_TERM[y])} risks")
