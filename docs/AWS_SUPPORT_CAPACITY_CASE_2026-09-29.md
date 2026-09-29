# AWS Support case: repeated g6.2xlarge capacity failures

**Submission status: received by AWS automated Support intake; human technical case BLOCKED by Basic Support.** Brad explicitly approved the exact payload, and it was sent on 29 September at approximately 17:48 UTC. The signed-in console matches the affected AWS account. Interaction ID: `0ca2dd14-33a4-4dec-8ecc-c90d368c465b`. Selecting Technical in the case form returned **"Technical case type is not available for your support plan."** The form showed Draft saved. No human case number was issued, no engineer response was obtained, and no paid support/trial or infrastructure change was made. [Open the support interaction](https://console.aws.amazon.com/support/home?interactionId=0ca2dd14-33a4-4dec-8ecc-c90d368c465b#/).

The [approved and sent payload](AWS_SUPPORT_CAPACITY_PAYLOAD_2026-09-29.txt) and [submission receipt](evidence/aws-runtime-bundle-2026-09-28/support-submission-2026-09-29.json) preserve the result. The prior automatic-approval rejection was resolved by Brad's explicit payload approval; the remaining block is AWS plan eligibility. An interaction/draft ID must not be reported as a human support case number.

The console offered Account and billing, Service limit increase, and Technical; Technical was unavailable under Basic Support. The issue was not misclassified as billing or a quota increase. The generic AI intake is not an engineering diagnosis of live capacity and supplies no guaranteed recovery time. Keep the saved draft; continue the separately scoped fallback qualification without purchasing support automatically.

## Subject

Repeated InsufficientInstanceCapacity for one g6.2xlarge in us-east-1; compatible GPU alternative requested

## Description

We are preparing a small non-production ML runtime on a single On-Demand Linux GPU instance. Repeated capacity errors are delaying development. We need only one running host, for a bounded session of at most 90 minutes; there is no production outage or fleet request.

Region: us-east-1. Instance type: g6.2xlarge, default tenancy, no placement group, capacity reservation preference open.

- Original: i-0e5e1cbc7b1367566, account zone us-east-1d / AZ ID use1-az6.
- Replacement: i-0439f5841d631d9f8, account zone us-east-1c / AZ ID use1-az4.

Both are currently stopped. Our Running On-Demand G and VT instances quota (L-DB2E81BA) is 8 vCPUs, enough for one g6.2xlarge, with no running or pending G/VT instance usage at the time checked. We are not attempting simultaneous starts.

Failures have been intermittent on 29 September 2026. The original successfully started at 05:35:30 UTC, and the replacement successfully restarted at 13:47:53 UTC. We stopped after setup/transfer problems under our cost guard. We are not attributing those setup problems to AWS capacity. The latest retries, at approximately 16:47 UTC, both failed with CloudTrail errorCode Server.InsufficientInstanceCapacity and errorMessage "Insufficient capacity."

Our two sequential AWS CLI invocations generated three service requests each. We will disable implicit retries on future start calls. Relevant CloudTrail request IDs (all 29 September UTC):

- Replacement, 16:47:23: 056839a0-e6d4-418d-943d-403ee0dd2cf1.
- Replacement, 16:47:24: adc5e7ff-192c-4ea9-b7a4-ed07b489b9e6.
- Replacement, 16:47:26: 51f4a74f-7972-42f4-a474-47db70b8c3dc.
- Original, 16:47:33: acbee627-0f71-4e1b-a0e5-3a95d95c601e.
- Original, 16:47:35: 1b9c9fe6-20a7-4df4-b499-1d4e10cbf172.
- Original, 16:47:37: fe276ed1-778e-4501-9abf-af8ba9e5fa5a.

Earlier new-launch attempts in account zones us-east-1a and us-east-1b also reported insufficient capacity before one replacement launch succeeded in us-east-1c. We understand an instance-type offering does not guarantee currently available capacity.

Please help us determine:

1. Do the above requests indicate an On-Demand g6.2xlarge hardware shortage in these AZ pools, or any additional account/configuration restriction?
2. Can you recommend a compatible alternative location or GPU type for one development host? Our preferred alternative is g5.2xlarge (A10G, 8 vCPU, 32 GiB RAM) in us-east-1; g6e.xlarge (L40S, 4 vCPU, 32 GiB RAM) is another candidate. We will qualify the software on any changed GPU.
3. Is there a known recovery estimate, or guidance beyond repeated identical restart attempts? We recognize that free capacity cannot be promised in advance.
4. If another region is recommended, what quota request and capacity planning steps should we take? Current G/VT quota in both us-east-2 and us-west-2 is zero.

Please do not create resources, modify our instances, start a fleet, or enroll us in paid support/reservations on our behalf. We are requesting diagnosis and guidance. We will authorize any subsequent infrastructure change separately.
