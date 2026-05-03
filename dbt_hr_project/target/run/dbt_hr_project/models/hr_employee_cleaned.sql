
  
    

        create or replace transient table RH_DB.GOLD.hr_employee_cleaned
         as
        (

with base as (

    select *
    from RH_DB.RAW.HR_RAW_DATA

),

-- 🔵 MEDIAN NUMÉRIQUES
stats as (

    select
        percentile_cont(0.5) within group (order by Age) as median_age,
        percentile_cont(0.5) within group (order by DailyRate) as median_dailyrate,
        percentile_cont(0.5) within group (order by DistanceFromHome) as median_distance,
        percentile_cont(0.5) within group (order by Education) as median_education,
        percentile_cont(0.5) within group (order by EnvironmentSatisfaction) as median_envsat,
        percentile_cont(0.5) within group (order by HourlyRate) as median_hourly,
        percentile_cont(0.5) within group (order by JobInvolvement) as median_jobinv,
        percentile_cont(0.5) within group (order by JobLevel) as median_joblevel,
        percentile_cont(0.5) within group (order by JobSatisfaction) as median_jobsat,
        percentile_cont(0.5) within group (order by MonthlyIncome) as median_income,
        percentile_cont(0.5) within group (order by MonthlyRate) as median_monthlyrate,
        percentile_cont(0.5) within group (order by NumCompaniesWorked) as median_numcomp,
        percentile_cont(0.5) within group (order by PercentSalaryHike) as median_salaryhike,
        percentile_cont(0.5) within group (order by PerformanceRating) as median_perf,
        percentile_cont(0.5) within group (order by RelationshipSatisfaction) as median_rel,
        percentile_cont(0.5) within group (order by StockOptionLevel) as median_stock,
        percentile_cont(0.5) within group (order by TotalWorkingYears) as median_totalyears,
        percentile_cont(0.5) within group (order by TrainingTimesLastYear) as median_training,
        percentile_cont(0.5) within group (order by WorkLifeBalance) as median_wlb,
        percentile_cont(0.5) within group (order by YearsAtCompany) as median_company,
        percentile_cont(0.5) within group (order by YearsInCurrentRole) as median_role,
        percentile_cont(0.5) within group (order by YearsSinceLastPromotion) as median_promo,
        percentile_cont(0.5) within group (order by YearsWithCurrManager) as median_manager

    from base

),

-- 🟢 MODE CATÉGORIELLES
mode_values as (

    select

        (select BusinessTravel
         from base
         where BusinessTravel is not null
         group by BusinessTravel
         order by count(*) desc limit 1) as mode_business_travel,

        (select Department
         from base
         where Department is not null
         group by Department
         order by count(*) desc limit 1) as mode_department,

        (select EducationField
         from base
         where EducationField is not null
         group by EducationField
         order by count(*) desc limit 1) as mode_educationfield,

        (select Gender
         from base
         where Gender is not null
         group by Gender
         order by count(*) desc limit 1) as mode_gender,

        (select JobRole
         from base
         where JobRole is not null
         group by JobRole
         order by count(*) desc limit 1) as mode_jobrole,

        (select MaritalStatus
         from base
         where MaritalStatus is not null
         group by MaritalStatus
         order by count(*) desc limit 1) as mode_marital,

        (select OverTime
         from base
         where OverTime is not null
         group by OverTime
         order by count(*) desc limit 1) as mode_overtime

)

select

    -- 🔥 TARGET
    b.Attrition,

    -- 🔵 NUMÉRIQUES (NULL → MEDIAN)
    coalesce(b.Age, s.median_age) as Age,
    coalesce(b.DailyRate, s.median_dailyrate) as DailyRate,
    coalesce(b.DistanceFromHome, s.median_distance) as DistanceFromHome,
    coalesce(b.Education, s.median_education) as Education,
    coalesce(b.EnvironmentSatisfaction, s.median_envsat) as EnvironmentSatisfaction,
    coalesce(b.HourlyRate, s.median_hourly) as HourlyRate,
    coalesce(b.JobInvolvement, s.median_jobinv) as JobInvolvement,
    coalesce(b.JobLevel, s.median_joblevel) as JobLevel,
    coalesce(b.JobSatisfaction, s.median_jobsat) as JobSatisfaction,
    coalesce(b.MonthlyIncome, s.median_income) as MonthlyIncome,
    coalesce(b.MonthlyRate, s.median_monthlyrate) as MonthlyRate,
    coalesce(b.NumCompaniesWorked, s.median_numcomp) as NumCompaniesWorked,
    coalesce(b.PercentSalaryHike, s.median_salaryhike) as PercentSalaryHike,
    coalesce(b.PerformanceRating, s.median_perf) as PerformanceRating,
    coalesce(b.RelationshipSatisfaction, s.median_rel) as RelationshipSatisfaction,
    coalesce(b.StockOptionLevel, s.median_stock) as StockOptionLevel,
    coalesce(b.TotalWorkingYears, s.median_totalyears) as TotalWorkingYears,
    coalesce(b.TrainingTimesLastYear, s.median_training) as TrainingTimesLastYear,
    coalesce(b.WorkLifeBalance, s.median_wlb) as WorkLifeBalance,
    coalesce(b.YearsAtCompany, s.median_company) as YearsAtCompany,
    coalesce(b.YearsInCurrentRole, s.median_role) as YearsInCurrentRole,
    coalesce(b.YearsSinceLastPromotion, s.median_promo) as YearsSinceLastPromotion,
    coalesce(b.YearsWithCurrManager, s.median_manager) as YearsWithCurrManager,

    -- 🟢 CATÉGORIELLES (NULL → MODE)
    coalesce(b.BusinessTravel, mv.mode_business_travel) as BusinessTravel,
    coalesce(b.Department, mv.mode_department) as Department,
    coalesce(b.EducationField, mv.mode_educationfield) as EducationField,
    coalesce(b.Gender, mv.mode_gender) as Gender,
    coalesce(b.JobRole, mv.mode_jobrole) as JobRole,
    coalesce(b.MaritalStatus, mv.mode_marital) as MaritalStatus,
    coalesce(b.OverTime, mv.mode_overtime) as OverTime

from base b
cross join stats s
cross join mode_values mv
        );
      
  