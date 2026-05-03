
  
    

        create or replace transient table RH_DB.GOLD.hr_employee_encoded
         as
        (

with base as (

    select *
    from RH_DB.GOLD.hr_employee_cleaned

)

select

    -- 🔥 TARGET
    Attrition,

    -- 🔵 NUMÉRIQUES (déjà clean)
    Age,
    DailyRate,
    DistanceFromHome,
    Education,
    EnvironmentSatisfaction,
    HourlyRate,
    JobInvolvement,
    JobLevel,
    JobSatisfaction,
    MonthlyIncome,
    MonthlyRate,
    NumCompaniesWorked,
    PercentSalaryHike,
    PerformanceRating,
    RelationshipSatisfaction,
    StockOptionLevel,
    TotalWorkingYears,
    TrainingTimesLastYear,
    WorkLifeBalance,
    YearsAtCompany,
    YearsInCurrentRole,
    YearsSinceLastPromotion,
    YearsWithCurrManager,

    -- 🟢 BUSINESS TRAVEL
    case when BusinessTravel = 'Travel_Rarely' then 1 else 0 end as BusinessTravel_Rarely,
    case when BusinessTravel = 'Travel_Frequently' then 1 else 0 end as BusinessTravel_Frequently,
    case when BusinessTravel = 'Non-Travel' then 1 else 0 end as BusinessTravel_NonTravel,

    -- 🟢 DEPARTMENT
    case when Department = 'Sales' then 1 else 0 end as Department_Sales,
    case when Department = 'Research & Development' then 1 else 0 end as Department_RnD,
    case when Department = 'Human Resources' then 1 else 0 end as Department_HR,

    -- 🟢 EDUCATION FIELD
    case when EducationField = 'Life Sciences' then 1 else 0 end as EducationField_LifeSciences,
    case when EducationField = 'Medical' then 1 else 0 end as EducationField_Medical,
    case when EducationField = 'Marketing' then 1 else 0 end as EducationField_Marketing,
    case when EducationField = 'Technical Degree' then 1 else 0 end as EducationField_Technical,
    case when EducationField = 'Other' then 1 else 0 end as EducationField_Other,
    case when EducationField = 'Human Resources' then 1 else 0 end as EducationField_HumanResources,

    -- 🟢 GENDER
    case when Gender = 'Male' then 1 else 0 end as Gender_Male,
    case when Gender = 'Female' then 1 else 0 end as Gender_Female,

    -- 🟢 JOB ROLE (IMPORTANT)
    case when JobRole = 'Sales Executive' then 1 else 0 end as JobRole_SalesExecutive,
    case when JobRole = 'Research Scientist' then 1 else 0 end as JobRole_ResearchScientist,
    case when JobRole = 'Laboratory Technician' then 1 else 0 end as JobRole_LaboratoryTechnician,
    case when JobRole = 'Manager' then 1 else 0 end as JobRole_Manager,
    case when JobRole = 'Healthcare Representative' then 1 else 0 end as JobRole_HealthcareRepresentative,
    case when JobRole = 'Manufacturing Director' then 1 else 0 end as JobRole_ManufacturingDirector,
    case when JobRole = 'Sales Representative' then 1 else 0 end as JobRole_SalesRepresentative,
    case when JobRole = 'Research Director' then 1 else 0 end as JobRole_ResearchDirector,
    case when JobRole = 'Human Resources' then 1 else 0 end as JobRole_HumanResources,

    -- 🟢 MARITAL STATUS
    case when MaritalStatus = 'Single' then 1 else 0 end as MaritalStatus_Single,
    case when MaritalStatus = 'Married' then 1 else 0 end as MaritalStatus_Married,
    case when MaritalStatus = 'Divorced' then 1 else 0 end as MaritalStatus_Divorced,

    -- 🟢 OVERTIME (TRÈS IMPORTANT POUR ATTRITION)
    case when OverTime = 'Yes' then 1 else 0 end as OverTime_Yes,
    case when OverTime = 'No' then 1 else 0 end as OverTime_No

from base
        );
      
  