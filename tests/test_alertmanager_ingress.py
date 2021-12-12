from tests.helm_template_generator import render_chart
import jmespath
import pytest
from . import supported_k8s_versions


def ingress_assertions_v1(doc):
    assert doc["apiVersion"] == "networking.k8s.io/v1"
    assert "RELEASE-NAME-alertmanager" in [
        name[0]
        for name in jmespath.search(
            "spec.rules[*].http.paths[*].backend.service.name", doc
        )
    ]
    assert "http" in [
        port[0]
        for port in jmespath.search(
            "spec.rules[*].http.paths[*].backend.service.port.name", doc
        )
    ]


def ingress_assertions_v1beta1(doc):
    assert doc["apiVersion"] == "networking.k8s.io/v1beta1"
    assert "RELEASE-NAME-alertmanager" in [
        name[0]
        for name in jmespath.search(
            "spec.rules[*].http.paths[*].backend.serviceName", doc
        )
    ]
    assert "http" in [
        port[0]
        for port in jmespath.search(
            "spec.rules[*].http.paths[*].backend.servicePort", doc
        )
    ]


@pytest.mark.parametrize(
    "kube_version",
    supported_k8s_versions,
)
class TestAlertmanagerIngress:
    def test_alertmanager_ingress_basic(self, kube_version):
        # sourcery skip: extract-duplicate-method
        docs = render_chart(
            kube_version=kube_version,
            show_only=["charts/alertmanager/templates/ingress.yaml"],
        )

        assert len(docs) == 1

        doc = docs[0]

        annotations = jmespath.search("metadata.annotations", doc)
        assert len(annotations) > 1
        assert annotations["kubernetes.io/ingress.class"] == "RELEASE-NAME-nginx"

        _, minor, _ = (int(x) for x in kube_version.split("."))

        if minor >= 19:
            ingress_assertions_v1(doc)

        if minor < 19:
            ingress_assertions_v1beta1(doc)

    def test_alertmanager_legacy_ingress(self, kube_version):
        """Test that networking.k8s.io/v1beta1 is always used with global.useLegacyIngress=True"""
        doc = render_chart(
            show_only=["charts/alertmanager/templates/ingress.yaml"],
            values={"global": {"useLegacyIngress": True}},
        )[0]

        ingress_assertions_v1beta1(doc)