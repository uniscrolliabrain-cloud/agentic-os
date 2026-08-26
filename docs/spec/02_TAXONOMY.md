# 02 — Taxonomía de capacidades digitales

Familia = agrupación taxonómica de capacidades. Cada familia contiene microacciones
cuyos contratos se definen en `08_MICROACTION_CATALOG.md`.

## Las 15 familias

### 01. WEB
SearchWeb, OpenURL, NavigateWebsite, ExtractPage, ExtractLinks, ExtractImages, ExtractTables, ExtractMetadata, DownloadResource, UploadResource, FillForm, SubmitForm, MonitorPage, DetectChange, CaptureScreenshot

### 02. RESEARCH
ResearchTopic, ResearchCompany, ResearchPerson, ResearchMarket, ResearchCompetitor, ResearchProduct, CompareEntities, FactCheck, CrossValidate, BuildSourceSet, ExtractClaims, BuildResearchReport

### 03. DOCUMENTS
CreateDocument, ReadDocument, ParseDocument, ExtractText, ExtractTables, TransformDocument, MergeDocuments, SplitDocument, ConvertFormat, GeneratePDF, GenerateDOCX, GenerateSpreadsheet, GeneratePresentation

### 04. DATA
ExtractData, CleanData, NormalizeData, Deduplicate, TransformData, JoinDatasets, FilterData, AggregateData, ClassifyData, ValidateData, ExportData, ImportData

### 05. CONTENT
GenerateBrief, GenerateOutline, WriteArticle, WriteEmail, WriteSocialPost, WriteAd, WriteScript, RewriteContent, TranslateContent, SummarizeContent, ExpandContent, RepurposeContent, GenerateMetadata

### 06. CREATIVE
GenerateImage, EditImage, GenerateVideo, GenerateAudio, GenerateVoice, GeneratePresentation, GenerateBrandAsset, ResizeAsset, ConvertAsset, OptimizeAsset

### 07. COMMUNICATION
CreateEmail, SendEmail, ReplyEmail, SearchMailbox, ReadEmail, ClassifyEmail, CreateMessage, SendMessage, ScheduleMessage, NotifyUser

### 08. SOCIAL
CreatePost, CreateCarousel, CreateReel, GenerateCaption, GenerateHashtags, SchedulePost, PublishPost, RetrieveMetrics, AnalyzePost, GenerateContentCalendar

### 09. CRM
CreateContact, UpdateContact, FindContact, CreateCompany, UpdateCompany, CreateLead, QualifyLead, AssignLead, CreateOpportunity, UpdateOpportunity, AddNote, CreateTask, UpdatePipeline

### 10. SALES
IdentifyProspects, EnrichProspect, ScoreLead, SegmentLeads, GenerateOutreach, PersonalizeOutreach, BuildSequence, TrackResponse, AnalyzePipeline, GenerateSalesReport

### 11. MARKETING
DefineAudience, DefinePositioning, CreateOffer, CreateCampaign, CreateCampaignBrief, GenerateContentPlan, GenerateAdVariants, GenerateLandingCopy, AnalyzeCampaign, OptimizeCampaign

### 12. SOFTWARE
CreateProject, InspectRepository, ReadCode, WriteCode, RefactorCode, GenerateComponent, GenerateAPI, GenerateSchema, GenerateTests, RunTests, Debug, Build, Deploy, Rollback, Monitor

### 13. DATABASE
ConnectDatabase, InspectSchema, QueryDatabase, InsertRecord, UpdateRecord, DeleteRecord, CreateTable, AlterSchema, MigrateDatabase, BackupDatabase, RestoreDatabase

### 14. AUTOMATION
CreateWorkflow, TriggerWorkflow, ScheduleWorkflow, ExecuteWorkflow, RouteTask, TransformPayload, CallAPI, HandleWebhook, RetryOperation, MonitorWorkflow

### 15. ANALYTICS
CollectMetrics, TransformMetrics, CalculateKPIs, DetectAnomaly, ComparePeriods, IdentifyTrend, GenerateChart, GenerateDashboard, GenerateReport, GenerateRecommendation

## Familias futuras (esqueleto a rellenar)

CALENDAR, PROJECT_MANAGEMENT, CLOUD, AUTH, PAYMENTS, ECOMMERCE, SUPPORT, KNOWLEDGE_BASE/RAG, VECTOR_DB, FILESYSTEM, GIT, API_GATEWAY, NOTIFICATIONS, FORMS, SCHEDULING, COMPLIANCE.

## Regla taxonómica

Toda microacción nueva debe encajar en una familia existente o crear una familia
nueva con justificación en `08_MICROACTION_CATALOG.md`. No se aceptan acciones
"sueltas".