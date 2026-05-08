-- ========================================
-- SCRIPT DE CRÉATION 
-- ========================================

-- 1. Créer l'entrepôt
CREATE WAREHOUSE RH_WH
WITH WAREHOUSE_SIZE = XSMALL
AUTO_SUSPEND = 60
AUTO_RESUME = TRUE;

-- 2. Créer la base de données
CREATE DATABASE RH_DB;

-- 3. Créer les schémas
CREATE SCHEMA RH_DB.RAW;
CREATE SCHEMA RH_DB.GOLD;

USE DATABASE RH_DB;
USE SCHEMA RAW;

-- 4. Créer la table HR_RAW_DATA
CREATE OR REPLACE TABLE RH_DB.RAW.HR_RAW_DATA (
    Age INT,
    Attrition STRING,
    BusinessTravel STRING,
    DailyRate INT,
    Department STRING,
    DistanceFromHome INT,
    Education INT,
    EducationField STRING,
    EmployeeCount INT,
    EmployeeNumber INT,
    EnvironmentSatisfaction INT,
    Gender STRING,
    HourlyRate INT,
    JobInvolvement INT,
    JobLevel INT,
    JobRole STRING,
    JobSatisfaction INT,
    MaritalStatus STRING,
    MonthlyIncome INT,
    MonthlyRate INT,
    NumCompaniesWorked INT,
    Over18 STRING,
    OverTime STRING,
    PercentSalaryHike INT,
    PerformanceRating INT,
    RelationshipSatisfaction INT,
    StandardHours INT,
    StockOptionLevel INT,
    TotalWorkingYears INT,
    TrainingTimesLastYear INT,
    WorkLifeBalance INT,
    YearsAtCompany INT,
    YearsInCurrentRole INT,
    YearsSinceLastPromotion INT,
    YearsWithCurrManager INT
);
SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME();
-- OU
SELECT CURRENT_ACCOUNT();
