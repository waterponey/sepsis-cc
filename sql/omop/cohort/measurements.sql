
--measurements for sepsis3 people 

--concept_id concept_name                                                
--3024929 	 Platelets [#/volume] in Blood by Automated count  				   
--3010834 	 Platelets [#/volume] in Blood by Manual count     				   
--3016723 	 Creatinine serum/plasma                           				   
--3018834 	 Bilirubin.total [Presence] in Urine by Test strip 			     
--3002113 	 Variant lymphocytes [Presence] in Blood by Light microscopy 

SELECT count(m.measurement_concept_id) FROM measurement m 
JOIN visit_occurrence vo on m.visit_occurrence_id = vo.visit_occurrence_id
where m.measurement_concept_id in (3024929, 3010834, 3016723, 3018834, 3002113) and vo.person_id IN (
    SELECT DISTINCT PERSON.PERSON_ID
    FROM COHORT, COHORT_DEFINITION, VISIT_OCCURRENCE, PERSON 
    WHERE lower(COHORT_DEFINITION.COHORT_DEFINITION_NAME) like lower('%sepsis3%') 
    AND COHORT.COHORT_DEFINITION_ID = COHORT_DEFINITION.COHORT_DEFINITION_ID 
    AND COHORT.SUBJECT_ID = VISIT_OCCURRENCE.VISIT_OCCURRENCE_ID 
    AND VISIT_OCCURRENCE.PERSON_ID = PERSON.PERSON_ID
)
