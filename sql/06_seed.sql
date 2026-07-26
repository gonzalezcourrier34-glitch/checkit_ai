-- ============================================================================
-- CheckIt.AI
-- Fichier : sql/06_seed.sql
-- Version : 1.0
-- Objet   : Jeu de données de démonstration pour tester les tables,
--           les vues, les KPI et les futures intégrations Airflow.
--
-- Prérequis :
--   - exécuter sql/00_database.sql ;
--   - exécuter sql/01_articles.sql ;
--   - exécuter sql/02_images_labels.sql ;
--   - exécuter sql/03_features_predictions.sql ;
--   - exécuter sql/04_indexes.sql ;
--   - exécuter sql/05_views.sql.
--
-- Le script est réexécutable.
-- Les données sont synthétiques et destinées uniquement aux tests.
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

SET search_path TO checkit, public;


-- ============================================================================
-- 1. Sources
-- ============================================================================

INSERT INTO checkit.sources (
    source_key,
    display_name,
    source_type,
    base_url,
    default_language,
    reliability_score,
    is_active,
    requires_api_key,
    refresh_interval_minutes,
    max_articles_per_run,
    configuration
)
VALUES
    (
        'bbc_news',
        'BBC News',
        'rss',
        'https://www.bbc.com/news',
        'en',
        0.900,
        TRUE,
        FALSE,
        60,
        100,
        '{"category": "general", "enabled": true}'::JSONB
    ),
    (
        'franceinfo',
        'France Info',
        'rss',
        'https://www.francetvinfo.fr',
        'fr',
        0.900,
        TRUE,
        FALSE,
        60,
        100,
        '{"category": "general", "enabled": true}'::JSONB
    ),
    (
        'newsdata',
        'NewsData.io',
        'api',
        'https://newsdata.io',
        'en',
        0.750,
        TRUE,
        TRUE,
        30,
        100,
        '{"languages": ["fr", "en"], "enabled": true}'::JSONB
    ),
    (
        'reddit',
        'Reddit',
        'social',
        'https://www.reddit.com',
        'en',
        0.500,
        TRUE,
        TRUE,
        30,
        100,
        '{"subreddits": ["worldnews", "technology"], "enabled": true}'::JSONB
    ),
    (
        'fakeddit',
        'Fakeddit',
        'dataset',
        NULL,
        'en',
        NULL,
        TRUE,
        FALSE,
        NULL,
        1000,
        '{"role": "multimodal_reference", "enabled": true}'::JSONB
    ),
    (
        'fakenewsnet',
        'FakeNewsNet',
        'dataset',
        NULL,
        'en',
        NULL,
        TRUE,
        FALSE,
        NULL,
        1000,
        '{"role": "labeled_reference", "enabled": true}'::JSONB
    )
ON CONFLICT (source_key)
DO UPDATE SET
    display_name = EXCLUDED.display_name,
    source_type = EXCLUDED.source_type,
    base_url = EXCLUDED.base_url,
    default_language = EXCLUDED.default_language,
    reliability_score = EXCLUDED.reliability_score,
    is_active = EXCLUDED.is_active,
    requires_api_key = EXCLUDED.requires_api_key,
    refresh_interval_minutes = EXCLUDED.refresh_interval_minutes,
    max_articles_per_run = EXCLUDED.max_articles_per_run,
    configuration = EXCLUDED.configuration;


-- ============================================================================
-- 2. Configuration du pipeline
-- ============================================================================

INSERT INTO checkit.pipeline_configuration (
    configuration_key,
    configuration_value,
    description,
    is_sensitive,
    is_active
)
VALUES
    (
        'max_articles_per_source',
        '100'::JSONB,
        'Nombre maximal d’articles collectés par source et par exécution.',
        FALSE,
        TRUE
    ),
    (
        'download_images',
        'true'::JSONB,
        'Active le téléchargement des images distantes.',
        FALSE,
        TRUE
    ),
    (
        'accepted_languages',
        '["fr", "en"]'::JSONB,
        'Langues acceptées par le pipeline de démonstration.',
        FALSE,
        TRUE
    ),
    (
        'request_timeout_seconds',
        '30'::JSONB,
        'Durée maximale d’attente d’une requête distante.',
        FALSE,
        TRUE
    ),
    (
        'min_title_length',
        '20'::JSONB,
        'Longueur minimale d’un titre valide.',
        FALSE,
        TRUE
    )
ON CONFLICT (configuration_key)
DO UPDATE SET
    configuration_value = EXCLUDED.configuration_value,
    description = EXCLUDED.description,
    is_sensitive = EXCLUDED.is_sensitive,
    is_active = EXCLUDED.is_active;


-- ============================================================================
-- 3. Exécution de pipeline de démonstration
-- ============================================================================

INSERT INTO checkit.pipeline_runs (
    id,
    dag_id,
    airflow_run_id,
    pipeline_name,
    pipeline_version,
    code_version,
    airflow_version,
    status,
    started_at,
    finished_at,
    extraction_duration_seconds,
    transformation_duration_seconds,
    load_duration_seconds,
    duration_seconds,
    extracted_count,
    transformed_count,
    valid_count,
    rejected_count,
    loaded_count,
    images_downloaded_count,
    images_valid_count,
    images_invalid_count,
    peak_memory_mb,
    average_cpu_percent,
    run_metadata
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'checkit_etl_pipeline',
    'manual__2026-07-13T14:00:00+00:00',
    'checkit_etl',
    '1.0.0',
    'demo-seed',
    '3.3.0',
    'success',
    '2026-07-13T14:00:00+00:00',
    '2026-07-13T14:00:12+00:00',
    5.200,
    3.100,
    1.400,
    9.700,
    6,
    6,
    5,
    1,
    5,
    4,
    3,
    1,
    256.000,
    42.50,
    '{"environment": "local", "seed": true}'::JSONB
)
ON CONFLICT (id)
DO UPDATE SET
    status = EXCLUDED.status,
    finished_at = EXCLUDED.finished_at,
    extracted_count = EXCLUDED.extracted_count,
    transformed_count = EXCLUDED.transformed_count,
    valid_count = EXCLUDED.valid_count,
    rejected_count = EXCLUDED.rejected_count,
    loaded_count = EXCLUDED.loaded_count,
    run_metadata = EXCLUDED.run_metadata;


-- ============================================================================
-- 4. Articles de démonstration
-- ============================================================================

INSERT INTO checkit.articles (
    id,
    source_id,
    pipeline_run_id,
    external_id,
    title,
    content,
    original_url,
    canonical_url,
    author,
    language,
    category,
    published_at,
    extracted_at,
    transformed_at,
    dataset_role,
    data_quality_status,
    rejection_reason,
    transformation_version,
    title_hash,
    content_hash,
    canonical_url_hash,
    raw_payload
)
VALUES
    (
        'demo_bbc_001',
        (SELECT id FROM checkit.sources WHERE source_key = 'bbc_news'),
        '00000000-0000-0000-0000-000000000001',
        'bbc-001',
        'International researchers publish a new climate report',
        'A group of international researchers released a report describing recent climate trends and the methods used to analyse them.',
        'https://example.org/bbc/climate-report',
        'https://example.org/bbc/climate-report',
        'BBC Science Desk',
        'en',
        'science',
        '2026-07-13T08:30:00+00:00',
        '2026-07-13T14:00:01+00:00',
        '2026-07-13T14:00:07+00:00',
        'acquisition',
        'valid',
        NULL,
        '1.0.0',
        md5('International researchers publish a new climate report'),
        md5('A group of international researchers released a report describing recent climate trends and the methods used to analyse them.'),
        md5('https://example.org/bbc/climate-report'),
        '{"demo": true}'::JSONB
    ),
    (
        'demo_franceinfo_001',
        (SELECT id FROM checkit.sources WHERE source_key = 'franceinfo'),
        '00000000-0000-0000-0000-000000000001',
        'franceinfo-001',
        'Une nouvelle ligne ferroviaire régionale entre en service',
        'La nouvelle ligne doit améliorer les déplacements quotidiens et réduire le temps de trajet entre plusieurs communes.',
        'https://example.org/franceinfo/ligne-ferroviaire',
        'https://example.org/franceinfo/ligne-ferroviaire',
        'Rédaction France Info',
        'fr',
        'transport',
        '2026-07-13T09:15:00+00:00',
        '2026-07-13T14:00:02+00:00',
        '2026-07-13T14:00:07+00:00',
        'acquisition',
        'valid',
        NULL,
        '1.0.0',
        md5('Une nouvelle ligne ferroviaire régionale entre en service'),
        md5('La nouvelle ligne doit améliorer les déplacements quotidiens et réduire le temps de trajet entre plusieurs communes.'),
        md5('https://example.org/franceinfo/ligne-ferroviaire'),
        '{"demo": true}'::JSONB
    ),
    (
        'demo_newsdata_001',
        (SELECT id FROM checkit.sources WHERE source_key = 'newsdata'),
        '00000000-0000-0000-0000-000000000001',
        'newsdata-001',
        'Viral post falsely claims that all bank cards will stop working',
        'The viral post provides no official source and contradicts statements published by banking institutions.',
        'https://example.org/newsdata/bank-card-rumour',
        'https://example.org/newsdata/bank-card-rumour',
        'Demo News Agency',
        'en',
        'fact-check',
        '2026-07-13T10:00:00+00:00',
        '2026-07-13T14:00:03+00:00',
        '2026-07-13T14:00:08+00:00',
        'fact_check_reference',
        'valid',
        NULL,
        '1.0.0',
        md5('Viral post falsely claims that all bank cards will stop working'),
        md5('The viral post provides no official source and contradicts statements published by banking institutions.'),
        md5('https://example.org/newsdata/bank-card-rumour'),
        '{"demo": true}'::JSONB
    ),
    (
        'demo_reddit_001',
        (SELECT id FROM checkit.sources WHERE source_key = 'reddit'),
        '00000000-0000-0000-0000-000000000001',
        'reddit-001',
        'Unverified image shared as proof of a major city event',
        'The publication reuses an old photograph and presents it as a recent event without providing a verifiable source.',
        'https://example.org/reddit/unverified-image',
        'https://example.org/reddit/unverified-image',
        'demo_user',
        'en',
        'social',
        '2026-07-13T10:30:00+00:00',
        '2026-07-13T14:00:04+00:00',
        '2026-07-13T14:00:08+00:00',
        'acquisition',
        'warning',
        NULL,
        '1.0.0',
        md5('Unverified image shared as proof of a major city event'),
        md5('The publication reuses an old photograph and presents it as a recent event without providing a verifiable source.'),
        md5('https://example.org/reddit/unverified-image'),
        '{"demo": true, "warning": "image provenance unclear"}'::JSONB
    ),
    (
        'demo_fakeddit_001',
        (SELECT id FROM checkit.sources WHERE source_key = 'fakeddit'),
        '00000000-0000-0000-0000-000000000001',
        'fakeddit-001',
        'Satirical article announces a fictional public holiday',
        'The publication is satirical and was created for entertainment, but it may be misunderstood when shared without context.',
        'https://example.org/fakeddit/fictional-holiday',
        'https://example.org/fakeddit/fictional-holiday',
        'Synthetic Dataset',
        'en',
        'satire',
        '2026-07-12T18:00:00+00:00',
        '2026-07-13T14:00:05+00:00',
        '2026-07-13T14:00:09+00:00',
        'multimodal_reference',
        'valid',
        NULL,
        '1.0.0',
        md5('Satirical article announces a fictional public holiday'),
        md5('The publication is satirical and was created for entertainment, but it may be misunderstood when shared without context.'),
        md5('https://example.org/fakeddit/fictional-holiday'),
        '{"demo": true}'::JSONB
    ),
    (
        'demo_invalid_001',
        (SELECT id FROM checkit.sources WHERE source_key = 'newsdata'),
        '00000000-0000-0000-0000-000000000001',
        'newsdata-invalid-001',
        'Incomplete publication retained for quality monitoring',
        '',
        NULL,
        NULL,
        NULL,
        'en',
        'unknown',
        NULL,
        '2026-07-13T14:00:06+00:00',
        NULL,
        'acquisition',
        'rejected',
        'missing_content_and_url',
        NULL,
        md5('Incomplete publication retained for quality monitoring'),
        NULL,
        NULL,
        '{"demo": true, "invalid": true}'::JSONB
    )
ON CONFLICT (id)
DO UPDATE SET
    title = EXCLUDED.title,
    content = EXCLUDED.content,
    data_quality_status = EXCLUDED.data_quality_status,
    rejection_reason = EXCLUDED.rejection_reason,
    updated_at = CURRENT_TIMESTAMP;


-- ============================================================================
-- 5. Images de démonstration
-- ============================================================================

INSERT INTO checkit.images (
    article_id,
    remote_url,
    local_path,
    file_name,
    file_extension,
    file_format,
    mime_type,
    width,
    height,
    aspect_ratio,
    size_bytes,
    file_hash,
    perceptual_hash,
    blur_score,
    brightness_score,
    entropy_score,
    download_duration_ms,
    image_position,
    is_primary,
    is_valid,
    validation_status,
    validation_error,
    association_status,
    association_score,
    association_method,
    downloaded_at,
    validated_at,
    associated_at,
    image_metadata
)
VALUES
    (
        'demo_bbc_001',
        'https://example.org/images/climate-report.jpg',
        'data/images/demo_bbc_001.jpg',
        'demo_bbc_001.jpg',
        'jpg',
        'JPEG',
        'image/jpeg',
        1200,
        800,
        1.500000,
        245000,
        md5('demo_bbc_001_image'),
        'aa11bb22cc33dd44',
        185.400000,
        128.200000,
        7.120000,
        320,
        0,
        TRUE,
        TRUE,
        'valid',
        NULL,
        'technical_match',
        1.0000,
        'filename',
        '2026-07-13T14:00:03+00:00',
        '2026-07-13T14:00:04+00:00',
        '2026-07-13T14:00:04+00:00',
        '{"demo": true}'::JSONB
    ),
    (
        'demo_franceinfo_001',
        'https://example.org/images/train.jpg',
        'data/images/demo_franceinfo_001.jpg',
        'demo_franceinfo_001.jpg',
        'jpg',
        'JPEG',
        'image/jpeg',
        1024,
        682,
        1.501466,
        198000,
        md5('demo_franceinfo_001_image'),
        'bb22cc33dd44ee55',
        142.800000,
        117.600000,
        6.980000,
        280,
        0,
        TRUE,
        TRUE,
        'valid',
        NULL,
        'technical_match',
        1.0000,
        'filename',
        '2026-07-13T14:00:04+00:00',
        '2026-07-13T14:00:05+00:00',
        '2026-07-13T14:00:05+00:00',
        '{"demo": true}'::JSONB
    ),
    (
        'demo_reddit_001',
        'https://example.org/images/reused-city.jpg',
        'data/images/demo_reddit_001.jpg',
        'demo_reddit_001.jpg',
        'jpg',
        'JPEG',
        'image/jpeg',
        800,
        600,
        1.333333,
        156000,
        md5('demo_reddit_001_image'),
        'cc33dd44ee55ff66',
        96.300000,
        101.500000,
        6.210000,
        410,
        0,
        TRUE,
        TRUE,
        'valid',
        NULL,
        'mismatch',
        0.2200,
        'manual',
        '2026-07-13T14:00:05+00:00',
        '2026-07-13T14:00:06+00:00',
        '2026-07-13T14:00:06+00:00',
        '{"demo": true, "reused_image": true}'::JSONB
    ),
    (
        'demo_fakeddit_001',
        'https://example.org/images/satire.png',
        'data/images/demo_fakeddit_001.png',
        'demo_fakeddit_001.png',
        'png',
        'PNG',
        'image/png',
        640,
        640,
        1.000000,
        122000,
        md5('demo_fakeddit_001_image'),
        'dd44ee55ff667788',
        131.000000,
        140.400000,
        7.440000,
        260,
        0,
        TRUE,
        TRUE,
        'valid',
        NULL,
        'semantic_match',
        0.9100,
        'clip',
        '2026-07-13T14:00:06+00:00',
        '2026-07-13T14:00:07+00:00',
        '2026-07-13T14:00:07+00:00',
        '{"demo": true}'::JSONB
    )
ON CONFLICT DO NOTHING;


-- ============================================================================
-- 6. Labels de démonstration
-- ============================================================================

INSERT INTO checkit.article_labels (
    article_id,
    label,
    label_type,
    label_source,
    annotator,
    annotation_method,
    confidence,
    is_ground_truth,
    is_active,
    notes,
    label_metadata
)
VALUES
    (
        'demo_bbc_001',
        'real',
        'manual',
        'demo_review',
        'reviewer_01',
        'manual_review',
        1.0000,
        TRUE,
        TRUE,
        'Article de démonstration considéré comme fiable.',
        '{"demo": true}'::JSONB
    ),
    (
        'demo_newsdata_001',
        'fake',
        'fact_check',
        'demo_fact_checker',
        'reviewer_02',
        'external_fact_check',
        0.9900,
        TRUE,
        TRUE,
        'La rumeur contredit les informations officielles.',
        '{"demo": true}'::JSONB
    ),
    (
        'demo_reddit_001',
        'misleading',
        'manual',
        'demo_review',
        'reviewer_02',
        'manual_review',
        0.9500,
        TRUE,
        TRUE,
        'L’image est ancienne et présentée hors contexte.',
        '{"demo": true}'::JSONB
    ),
    (
        'demo_fakeddit_001',
        'satire',
        'dataset',
        'Fakeddit',
        NULL,
        'dataset_import',
        1.0000,
        TRUE,
        TRUE,
        'Label issu du dataset de démonstration.',
        '{"demo": true}'::JSONB
    )
ON CONFLICT (
    article_id,
    label,
    label_type,
    label_source
)
DO UPDATE SET
    confidence = EXCLUDED.confidence,
    is_ground_truth = EXCLUDED.is_ground_truth,
    is_active = EXCLUDED.is_active,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;


-- ============================================================================
-- 7. Features de démonstration
-- ============================================================================

INSERT INTO checkit.article_features (
    article_id,
    image_id,
    pipeline_run_id,
    feature_group,
    feature_name,
    feature_type,
    feature_version,
    producer_name,
    producer_version,
    numeric_value,
    text_value,
    boolean_value,
    json_value,
    vector_path,
    vector_dimension,
    confidence,
    feature_metadata
)
VALUES
    (
        'demo_bbc_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'nlp',
        'title_length',
        'numeric',
        '1.0',
        'feature_generator',
        '1.0.0',
        58,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        '{"unit": "characters"}'::JSONB
    ),
    (
        'demo_bbc_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'nlp',
        'sentiment',
        'text',
        '1.0',
        'demo_sentiment_model',
        '1.0',
        NULL,
        'neutral',
        NULL,
        NULL,
        NULL,
        NULL,
        0.8700,
        '{"demo": true}'::JSONB
    ),
    (
        'demo_newsdata_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'quality',
        'clickbait_score',
        'numeric',
        '1.0',
        'demo_quality_model',
        '1.0',
        0.7800,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0.9000,
        '{"demo": true}'::JSONB
    ),
    (
        'demo_reddit_001',
        (SELECT id FROM checkit.images WHERE article_id = 'demo_reddit_001' LIMIT 1),
        '00000000-0000-0000-0000-000000000001',
        'vision',
        'image_reuse_risk',
        'numeric',
        '1.0',
        'demo_image_model',
        '1.0',
        0.8800,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0.9200,
        '{"demo": true}'::JSONB
    ),
    (
        'demo_fakeddit_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'embedding',
        'text_embedding',
        'vector_path',
        '1.0',
        'sentence-transformers',
        'demo-v1',
        NULL,
        NULL,
        NULL,
        NULL,
        'data/embeddings/demo_fakeddit_001.npy',
        384,
        NULL,
        '{"demo": true}'::JSONB
    )
ON CONFLICT DO NOTHING;


-- ============================================================================
-- 8. Prédictions de démonstration
-- ============================================================================

INSERT INTO checkit.model_predictions (
    article_id,
    image_id,
    pipeline_run_id,
    model_name,
    model_version,
    task_type,
    feature_set_version,
    predicted_label,
    confidence,
    decision_threshold,
    probabilities,
    explanation,
    prediction_status
)
VALUES
    (
        'demo_bbc_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'DemoFakeNewsClassifier',
        '1.0',
        'fake_news_classification',
        'features_v1',
        'real',
        0.9100,
        0.5000,
        '{"real": 0.91, "fake": 0.09}'::JSONB,
        '{"important_signals": ["named source", "neutral wording"]}'::JSONB,
        'success'
    ),
    (
        'demo_newsdata_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'DemoFakeNewsClassifier',
        '1.0',
        'fake_news_classification',
        'features_v1',
        'fake',
        0.9400,
        0.5000,
        '{"real": 0.06, "fake": 0.94}'::JSONB,
        '{"important_signals": ["viral claim", "absence of official source"]}'::JSONB,
        'success'
    ),
    (
        'demo_reddit_001',
        (SELECT id FROM checkit.images WHERE article_id = 'demo_reddit_001' LIMIT 1),
        '00000000-0000-0000-0000-000000000001',
        'DemoMultimodalClassifier',
        '1.0',
        'multimodal_classification',
        'features_v1',
        'misleading',
        0.8800,
        0.5000,
        '{"real": 0.05, "fake": 0.07, "misleading": 0.88}'::JSONB,
        '{"image_context": "old image reused", "text_image_similarity": 0.22}'::JSONB,
        'success'
    ),
    (
        'demo_fakeddit_001',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        'DemoFakeNewsClassifier',
        '1.0',
        'fake_news_classification',
        'features_v1',
        'satire',
        0.8600,
        0.5000,
        '{"real": 0.04, "fake": 0.10, "satire": 0.86}'::JSONB,
        '{"important_signals": ["humorous framing", "fictional event"]}'::JSONB,
        'success'
    )
ON CONFLICT DO NOTHING;


-- ============================================================================
-- 9. Métriques du pipeline
-- ============================================================================

INSERT INTO checkit.pipeline_metrics (
    pipeline_run_id,
    metric_name,
    metric_value,
    metric_unit,
    component,
    metric_metadata
)
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'valid_article_rate',
        83.333333,
        'percent',
        'validation',
        '{"demo": true}'::JSONB
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'image_validation_rate',
        75.000000,
        'percent',
        'image_service',
        '{"demo": true}'::JSONB
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'pipeline_duration',
        9.700000,
        'seconds',
        'pipeline',
        '{"demo": true}'::JSONB
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'loaded_article_count',
        5.000000,
        'articles',
        'load',
        '{"demo": true}'::JSONB
    )
ON CONFLICT DO NOTHING;


-- ============================================================================
-- 10. Logs ETL
-- ============================================================================

INSERT INTO checkit.etl_logs (
    pipeline_run_id,
    log_level,
    component,
    message,
    error_type,
    error_details,
    created_at
)
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'INFO',
        'extract',
        'Extraction de démonstration terminée.',
        NULL,
        '{}'::JSONB,
        '2026-07-13T14:00:05+00:00'
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'WARNING',
        'image_service',
        'Une image présente une association texte-image incohérente.',
        NULL,
        '{"article_id": "demo_reddit_001"}'::JSONB,
        '2026-07-13T14:00:07+00:00'
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'ERROR',
        'validation',
        'Un article a été rejeté pendant la validation.',
        'ArticleValidationError',
        '{"article_id": "demo_invalid_001", "reason": "missing_content_and_url"}'::JSONB,
        '2026-07-13T14:00:08+00:00'
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'INFO',
        'load',
        'Chargement PostgreSQL terminé avec succès.',
        NULL,
        '{"loaded_count": 5}'::JSONB,
        '2026-07-13T14:00:12+00:00'
    )
ON CONFLICT DO NOTHING;


-- ============================================================================
-- 11. Version du dataset
-- ============================================================================

INSERT INTO checkit.dataset_versions (
    id,
    version_name,
    pipeline_run_id,
    description,
    article_count,
    image_count,
    label_count,
    dataset_path,
    checksum
)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    'demo_dataset_v1',
    '00000000-0000-0000-0000-000000000001',
    'Jeu de données synthétique utilisé pour tester PostgreSQL, Airflow et les vues.',
    6,
    4,
    4,
    'data/processed/demo_dataset_v1',
    md5('demo_dataset_v1')
)
ON CONFLICT (version_name)
DO UPDATE SET
    article_count = EXCLUDED.article_count,
    image_count = EXCLUDED.image_count,
    label_count = EXCLUDED.label_count,
    dataset_path = EXCLUDED.dataset_path;


COMMIT;


-- ============================================================================
-- 12. Vérification
-- ============================================================================

SELECT 'sources' AS object_name, COUNT(*) AS row_count
FROM checkit.sources

UNION ALL

SELECT 'pipeline_runs', COUNT(*)
FROM checkit.pipeline_runs

UNION ALL

SELECT 'articles', COUNT(*)
FROM checkit.articles

UNION ALL

SELECT 'images', COUNT(*)
FROM checkit.images

UNION ALL

SELECT 'article_labels', COUNT(*)
FROM checkit.article_labels

UNION ALL

SELECT 'article_features', COUNT(*)
FROM checkit.article_features

UNION ALL

SELECT 'model_predictions', COUNT(*)
FROM checkit.model_predictions

UNION ALL

SELECT 'pipeline_metrics', COUNT(*)
FROM checkit.pipeline_metrics

UNION ALL

SELECT 'etl_logs', COUNT(*)
FROM checkit.etl_logs

UNION ALL

SELECT 'dataset_versions', COUNT(*)
FROM checkit.dataset_versions;