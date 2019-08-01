<template>
  <button-info popup_title="RECONCILED CLUSTER VISUALIZATION">
    <div class="text-left">
      <div class="h2">Reconciling an ILN</div>

      <p class="h5 pt-4 pl-5">
        We enable the reconciliation of an ILN using relations between discovered ILN. For the current
        example, the relation used is the marital status meaning married people. In this example, the ILN to
        reconcile is the one of <strong>Meulder Hans</strong>. It is the one in <strong>blue</strong> and it
        connect to two other clusters using purple dotted lines. Reading the graph, the other two clusters
        indicate that <strong>Meulder Hans</strong> appears to be connected to two women: **Petsinck
        Catharina (orange)<strong> and </strong>Jans Fijtje (green)**.
      </p>

      <p class="h5 pt-4 pl-5">
        We provide two representation where the first picture presents a compact representation of all
        clusters while the second representation presents a non compact representation of the investigated
        cluster: <strong>Meulder Hans</strong>.
      </p>

      <p class="h5 pt-4 pl-5">
        Now, given this additional marital status, is it plausible that all nodes representing <strong>Meulder
        Hans</strong> are indeed representing the same person?
      </p>

      <p class="h5 pt-4 pl-5">
        To answer this questions, we make use of the existence of <strong>cycle</strong> to materialise
        strong evidence.
      </p>

      <div class="text-center pt-4">
        <img src="/static/images/4 Meulder Hans (Cluster-Compact Compact-Evidence).jpg" width="900"/>
      </div>

      <div class="text-center pt-4">
        <img src="/static/images/5 Meulder Hans (Cluster-Compact Evidence).jpg" width="900"/>
      </div>

      <div class="h2 pt-4">Reconciled Nodes</div>
    </div>
  </button-info>
</template>