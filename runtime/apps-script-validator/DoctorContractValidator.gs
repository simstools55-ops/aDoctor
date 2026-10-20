/**
 * SIMS Doctor Contract Validator v0.1.0
 * Apps Script compatible lightweight envelope validator.
 */
const SIMS_DOCTOR_SUPPORTED_CONTRACTS = Object.freeze({
  SIMS_DOCTOR_ARTICLE_CATALOG_V1: '1.0',
  SIMS_DOCTOR_LONG_TERM_SNAPSHOT_V1: '1.0',
  SIMS_DOCTOR_CASE_DIAGNOSIS_V1: '1.0',
  SIMS_DOCTOR_WRITER_REQUEST_V1: '1.0',
  SIMS_TREATMENT_RESULT_V1: '1.0',
  SIMS_DOCTOR_CASE_RESULT_V1: '1.0'
});

function simsValidateDoctorEnvelope_(payload, expectedFormat) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return simsDoctorValidationResult_(false, [{
      code: 'PAYLOAD_NOT_OBJECT',
      field: '$',
      message: 'JSONオブジェクトではありません。'
    }]);
  }

  const required = [
    'format', 'contract_version', 'schema_version', 'source_system',
    'target_system', 'message_id', 'generated_at', 'timezone', 'site'
  ];

  required.forEach(function(field) {
    if (payload[field] === undefined || payload[field] === null || payload[field] === '') {
      errors.push({
        code: 'REQUIRED_FIELD_MISSING',
        field: field,
        message: field + ' は必須です。'
      });
    }
  });

  if (expectedFormat && payload.format !== expectedFormat) {
    errors.push({
      code: 'FORMAT_MISMATCH',
      field: 'format',
      message: '期待するformatは ' + expectedFormat + ' です。'
    });
  }

  const supported = SIMS_DOCTOR_SUPPORTED_CONTRACTS[payload.format];
  if (!supported) {
    errors.push({
      code: 'UNSUPPORTED_FORMAT',
      field: 'format',
      message: '未対応の契約形式です。'
    });
  } else if (payload.contract_version !== supported) {
    errors.push({
      code: 'VERSION_MISMATCH',
      field: 'contract_version',
      message: '対応contract_versionは ' + supported + ' です。'
    });
  }

  if (payload.timezone && payload.timezone !== 'Asia/Tokyo') {
    errors.push({
      code: 'TIMEZONE_MISMATCH',
      field: 'timezone',
      message: 'timezoneはAsia/Tokyoを使用してください。'
    });
  }

  if (payload.site && !payload.site.site_id) {
    errors.push({
      code: 'SITE_ID_MISSING',
      field: 'site.site_id',
      message: 'site.site_idは必須です。'
    });
  }

  return simsDoctorValidationResult_(errors.length === 0, errors);
}

function simsDoctorValidationResult_(valid, errors) {
  return {
    valid: valid,
    errors: errors || []
  };
}

function simsParseAndValidateDoctorJson_(jsonText, expectedFormat) {
  try {
    const payload = JSON.parse(jsonText);
    const validation = simsValidateDoctorEnvelope_(payload, expectedFormat);
    return {
      success: validation.valid,
      payload: validation.valid ? payload : null,
      errors: validation.errors
    };
  } catch (error) {
    return {
      success: false,
      payload: null,
      errors: [{
        code: 'INVALID_JSON',
        field: '$',
        message: 'JSONを解析できません: ' + error.message
      }]
    };
  }
}
