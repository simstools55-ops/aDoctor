/**
 * Lightweight SBM-side validation helpers for SIMS Doctor batch contracts.
 * This is not a replacement for JSON Schema validation on the Doctor side.
 */
function validateSbmDoctorBatchAcceptedV1_(value) {
  if (!value || value.contract_name !== 'SIMS_SBM_DOCTOR_BATCH_ACCEPTED_V1') {
    throw new Error('Invalid Doctor batch accepted contract.');
  }
  if (value.contract_version !== '1.0' || !value.queue_record_id) {
    throw new Error('Unsupported Doctor batch accepted contract.');
  }
  return true;
}

function validateSbmDoctorBatchStatusV1_(value) {
  if (!value || value.contract_name !== 'SIMS_SBM_DOCTOR_BATCH_STATUS_V1') {
    throw new Error('Invalid Doctor batch status contract.');
  }
  if (!value.progress || typeof value.result_ready !== 'boolean') {
    throw new Error('Incomplete Doctor batch status contract.');
  }
  return true;
}

function validateSbmDoctorBatchResultPackageV1_(value) {
  if (!value || value.contract_name !== 'SIMS_SBM_DOCTOR_BATCH_RESULT_PACKAGE_V1') {
    throw new Error('Invalid Doctor batch result package.');
  }
  if (!value.result_fingerprint || !Array.isArray(value.items)) {
    throw new Error('Incomplete Doctor batch result package.');
  }
  return true;
}
