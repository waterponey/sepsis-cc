import pandas as pd
import numpy as np

gby = 'visit_occurrence_id'



creatine_too_high_level = 4
creatine_absolut_increase = 0.3
creatine_absolut_increase_days = np.timedelta64(2, 'D')

creatine_relative_increase = 1.5
creatine_concept_id = 3016723

def detect_creatine_to_high(dates, creatine_levels):
    too_high_creatines = creatine_levels > creatine_too_high_level
    if sum(too_high_creatines) == 0:
        return None
    else:
        first_index = np.argmax(too_high_creatines)
        return first_index


def detect_creatine_absolut_increase(dates, creatine_levels, absolut_increase,
                                     max_date):
    initial_creatine = creatine_levels[0]
    considered_period = dates < max_date
    significative_increase = creatine_levels[
                                 considered_period] > initial_creatine + absolut_increase
    if sum(significative_increase) == 0:
        return None
    else:
        first_index = np.argmax(significative_increase)
        return first_index


def detect_creatine_relative_increase(dates, creatine_levels,
                                      relative_increase):
    initial_creatine = creatine_levels[0]
    significative_increase = (creatine_levels / initial_creatine) > relative_increase
    if sum(significative_increase) == 0:
        return None
    else:
        first_index = np.argmax(significative_increase)
        return first_index


def detect_aki(dates, creatine_levels):
    date_too_high = detect_creatine_to_high(dates, creatine_levels)
    date_absolut = detect_creatine_absolut_increase(dates, creatine_levels,
                                                    creatine_absolut_increase,
                                                    creatine_absolut_increase_days)
    date_relative = detect_creatine_relative_increase(dates, creatine_levels,
                                                      creatine_relative_increase)
    detect_dates = np.array([date_too_high, date_absolut, date_relative])

    if sum(detect_dates != None) > 0:
        first_detect_date_index = detect_dates[detect_dates != None].min()
        if date_too_high == first_detect_date_index:
            cause = 'too high'
        elif date_relative == first_detect_date_index:
            cause = 'relative'
        elif date_absolut == first_detect_date_index:
            cause = 'absolut'
        else:
            raise ValueError('cannot find date')

        return first_detect_date_index, cause

    else:
        return None, None


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
        x.columns = ['drug_%s' %c for c in x.columns]
        self.patient = self.patient.join(x)
        return self
    
    def with_n_measurment(self, meas):
        x = meas.groupby([gby, 'measurement_concept_id']).person_id.count().unstack().fillna(0).astype(np.int32)
        self.patient = self.patient.join(x)
        return self
    
    def with_measurements(self, meas):
        
        for cid in meas.measurement_concept_id.unique():
            print(cid)
            subs = meas.loc[meas.measurement_concept_id == cid, [gby, 'value_source_value']]
            label = 'measur_%d' % cid
            
            try:
                subs['code'] = subs.value_source_value.astype(np.float64)
                categ = False
            except ValueError:
                subs['code'] = subs.value_source_value.astype('category').cat.codes
                categ = True
            gr = subs.groupby(gby)
            
            if categ:
                out = gr.apply(lambda x: pd.Series({'%s_first' %label: x.code.iloc[0],
                                                    '%s_last' %label: x.code.iloc[-1]})) 
            else:  
                out = gr.apply(lambda x: pd.Series({'%s_first' %label: x.code.iloc[0],
                                                    '%s_last' %label: x.code.iloc[-1], 
                                                    '%s_max' %label: x.code.max(),
                                                    '%s_min' %label: x.code.min()}))
        
            self.patient = self.patient.join(out, how='left')
        return self

    def with_infection_date(self, infections):
        date_col = 'condition_start_datetime'
        infections[date_col] = infections[date_col].astype('datetime64[ns]')
        first_infection = infections.groupby('visit_occurrence_id', as_index=False)[date_col].min()
        self.patient = self.patient.merge(first_infection, how='left',
                                          left_on='visit_id',
                                          right_on='visit_occurrence_id')
        self.patient = self.patient.drop('visit_occurrence_id', axis=1)
        self.patient = self.patient.rename(
            columns={'condition_start_datetime': 'infection_date'})
        return self

    def with_features(self):
        pass

    def _acute_kidney_injury_visit(self, visit_id, meas):
        concept_person_df = meas[
            (meas['measurement_concept_id'] == creatine_concept_id)
            & (meas['visit_occurrence_id'] == visit_id)]

        # sort by measurement date
        concept_person_df = concept_person_df.sort_values('measurement_datetime')

        # remove non float measurement values
        concept_person_df['value_source_value'] = pd.to_numeric(
            concept_person_df['value_source_value'], errors='coerce')

        # print(    concept_person_df['value_source_value'])
        # concept_person_df = concept_person_df.dropna('value_source_value')
        concept_person_df = concept_person_df[
            concept_person_df['value_source_value'] != np.nan]

        dates = concept_person_df['measurement_datetime'].values
        if len(dates) == 0:
            return None, 'no creatine'
        dates = dates.astype('datetime64[ns]')

        first_measurement_date = min(dates)
        shifted_dates = dates - first_measurement_date
        shifted_dates = shifted_dates.astype('timedelta64[h]')
        values = concept_person_df['value_source_value'].values
        values = values.astype(float)

        aki_date_index, cause = detect_aki(shifted_dates, values)
        if aki_date_index is None:
            aki_date = None
        else:
            aki_date = dates[aki_date_index]

        infection_date = \
        concept_person_df['infection_date'].astype('datetime64[ns]').values[0]

        if aki_date is None:
            return None, 'no aki'

        if infection_date == np.datetime64('NaT'):
            return None, 'no infection'

        if aki_date < infection_date:
            return None, 'aki before infection'

        return aki_date, cause

    def with_acute_kidney_injury(self, meas, infections):

        meas = meas.merge(self.patient, left_on='visit_occurrence_id',
                          right_on='visit_id', how='left')

        for index, row in self.patient.iterrows():
            if index % 250 == 0:
                print(index, '/', self.patient.shape[0])
            visit_id = row['visit_id']
            aki_datetime, aki_cause = self._acute_kidney_injury_visit(visit_id, meas)
            self.patient.loc[index, 'aki_datetime'] = aki_datetime
            self.patient.loc[index, 'aki_cause'] = aki_cause

        return self

