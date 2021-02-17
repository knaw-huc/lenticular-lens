<template>
  <button-info popup_title="MATCHING METHODS AND LOGICAL OPERATOR">
    <div class="h3 pt-5 text-secondary">Simple Matching Scenario-1</div>
    <img width="700px" src="/static/images/4_MethodSimple.png">

    <div class="h5">Matching two datasets using <strong>one</strong> property per dataset</div>

    <div class="h3 pt-5 text-secondary">Simple Matching Scenario-2</div>
    <img width="700px" src="/static/images/5_MethodProp.png">

    <div class="h5">
      More than one property per dataset is allowed.<br>
      Only, all aligned property should be semantically similar.
    </div>

    <div class="h3 pt-5 text-secondary">
      Simple Matching Scenario-3
    </div>
    <img width="700px" src="/static/images/6_MethodDs.png">

    <div class="h5">
      More than one dataset is allowed for a <span class="text-secondary">SOURCE</span> or a
      <span class="text-secondary">TARGET</span>.<br>
      Only, all aligned property should be semantically similar.<br>
      The logical expression provide a human readable of how it is implemented.
    </div>

    <div class="h3 pt-5 text-secondary">Complex Matching Scenario</div>
    <img width="700px" src="/static/images/7_MethodFull.png">

    <div class="h5">
      More than one method is allowed.<br>
      Within each method, a <strong>DISJUNCTION</strong> (<span class="text-secondary">OR</span>) operator is
      applied over each pair of properties <strong>across</strong> two datasets.<br>
      A <strong>DISJUNCTION</strong> (<span class="text-secondary">OR</span>) OR <strong>CONJUNCTION</strong>
      (<span class="text-secondary">AND</span>) operator is necessary whenever more than one methods is
      required.<br>
    </div>
  </button-info>
</template>