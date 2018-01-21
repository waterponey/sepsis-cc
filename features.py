import pandas as pd
import numpy as np


gby = 'visit_occurrence_id'

def to_code_plaquette_smear(x):
    
    plaquette_smear_codes = {'UNABLE TO ESTIMATE DUE TO PLATELET CLUMPS': -1,
                         'RARE': 0, 'VERY LOW': 1, 'LOW': 2,
                         'NORMAL': 3, 'HIGH': 4, 'VERY HIGH': 5}
    out = np.zeros(len(x), dtype=np.int32)
    for k,v in plaquette_smear_codes.items():
        out[x == k] = v
    return out


class MyDataFrame(object):

    def __init__(self, patient):
        self.patient = patient

    def with_age(self, visit):
        visit['age'] = visit.visit_start_date.dt.year - visit.year_of_birth
        self.patient['age'] = visit.groupby(gby).age.mean()
        self.patient.loc[self.patient.age > 200, 'age'] = 90
        return self

    def with_death(self, visit):
        self.patient['has_died'] = visit.groupby(gby).death_date.apply(lambda x: x.notnull().any())
        return self

    def with_gender_ismale(self, visit):
        """True for male patients False for females"""
        self.patient['is_male'] = visit.groupby(gby).gender_source_value.apply(lambda x: (x == 'M').all())
        return self

    def with_race(self, visit):
        """Categorical values for ethnics"""
        self.patient['race'] = visit.groupby(gby).race_source_value.astype('category')
        self.patient['race'] = self.patient['race'].cat.codes
        return self

    def with_n_unique_drugs(self, visit):
        """Number of different drugs given to the patient"""
        self.patient['n_unique_drugs'] = visit.groupby(gby).drug_concept_id.apply(lambda x: (np.unique(x)!=0).sum())
        return self

    def with_n_drugs(self, visit):
        """ Total number of drugs give to the patient"""
        self.patient['n_drugs'] = visit.groupby(gby).drug_concept_id.apply(lambda x: (x!=0).sum())
        return self

    def with_n_administration_per_drug(self, visit):
        """ Number of drug administration for each drug in the dataset"""
        x = visit.groupby([gby, 'drug_concept_id']).person_id.count().unstack().fillna(0).astype(np.int32)
        self.patient = self.patient.join(x)
        return self

    def with_n_measurment(self, meas):
        x = meas.groupby([gby, 'measurement_concept_id']).person_id.count().unstack().fillna(0).astype(np.int32)
        self.patient = self.patient.join(x)
        return self

    def with_lymphocites(self, meas):
        """ Not useful in practice"""
        gr = meas.loc[meas.measurement_concept_id == 3002113].groupby(gby)
        out = gr.apply(lambda x: pd.Series({'lympho_max': x.value_as_number.max(),
                                            'lympho_min': x.value_as_number.min(),
                                            'lympho_first': x.value_as_number.iloc[0],
                                            'lympho_last': x.value_as_number.iloc[-1]}))
        self.patient = self.patient.join(out, how='left')
        return self

    def with_plaquette_smear(self, meas):

        subs = meas.loc[meas.measurement_concept_id == 3010834, [gby, 'value_source_value']]
        subs['code'] = to_code_plaquette_smear(subs.value_source_value)
        gr = subs.groupby(gby)
        out = gr.apply(lambda x: pd.Series({'plaq_sm_max': x.code.max(),
                                            'plaq_sm_min': x.code.min(),
                                            'plaq_sm_first': x.code.iloc[0],
                                            'plaq_sm_last': x.code.iloc[-1]}))

        self.patient = self.patient.join(out, how='left')
        return self

    def with_plaquete_count(self, meas):
        """ Platelet count features """
        subs = meas.loc[meas.measurement_source_value == 'Platelet Count', [gby, 'value_source_value']]
        gr = subs.groupby(gby)
        out = gr.apply(lambda x: pd.Series({'plaq_nb_max': x.code.max(),
                                            'plaq_nb_min': x.code.min(),
                                            'plaq_nb_first': x.code.iloc[0],
                                            'plaq_nb_last': x.code.iloc[-1]}))
        self.patient = self.patient.join(out, how='left')
        return self


    def with_features(self):
        pass
