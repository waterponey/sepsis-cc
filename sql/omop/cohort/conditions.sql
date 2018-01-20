--conditions of people in sepsis3
select C.concept_name, COUNT(*)
from concept C, condition_occurrence CO
where CO.condition_concept_id = C.concept_id
and co.person_id IN (
    SELECT DISTINCT PERSON.PERSON_ID
    FROM COHORT, COHORT_DEFINITION, VISIT_OCCURRENCE, PERSON 
    WHERE lower(COHORT_DEFINITION.COHORT_DEFINITION_NAME) like lower('%sepsis3%') 
    AND COHORT.COHORT_DEFINITION_ID = COHORT_DEFINITION.COHORT_DEFINITION_ID 
    AND COHORT.SUBJECT_ID = VISIT_OCCURRENCE.VISIT_OCCURRENCE_ID 
    AND VISIT_OCCURRENCE.PERSON_ID = PERSON.PERSON_ID
)
group by C.concept_name ORDER BY count(1) desc 
limit 100
