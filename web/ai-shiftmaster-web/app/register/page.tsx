'use client';

import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Alert,
  Space,
  Steps,
  Select,
  Checkbox,
  Row,
  Col,
  Divider,
  message,
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  BankOutlined,
  PhoneOutlined,
  GlobalOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface CompanyFormData {
  companyName: string;
  industry: string;
  employeeCount: string;
  country: string;
  city: string;
  address: string;
  phone: string;
  website?: string;
}

interface AdminFormData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  jobTitle: string;
}

interface PlanFormData {
  plan: string;
  agreeTerms: boolean;
  agreePrivacy: boolean;
  newsletter: boolean;
}

export default function RegisterPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [companyForm] = Form.useForm();
  const [adminForm] = Form.useForm();
  const [planForm] = Form.useForm();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const [companyData, setCompanyData] = useState<CompanyFormData | null>(null);
  const [adminData, setAdminData] = useState<AdminFormData | null>(null);

  const industries = [
    'Teknoloji',
    'Sağlık',
    'Üretim',
    'Perakende',
    'Lojistik',
    'Finans',
    'Eğitim',
    'Hizmet',
    'İnşaat',
    'Enerji',
    'Tarım',
    'Diğer',
  ];

  const employeeCounts = [
    '1-10',
    '11-50',
    '51-100',
    '101-250',
    '251-500',
    '501-1000',
    '1000+',
  ];

  const plans = [
    {
      key: 'starter',
      name: 'Başlangıç',
      price: '₺999/ay',
      features: ['25 çalışana kadar', 'Temel vardiya planlama', 'E-posta desteği'],
    },
    {
      key: 'professional',
      name: 'Profesyonel',
      price: '₺2,499/ay',
      features: ['100 çalışana kadar', 'AI destekli optimizasyon', 'Öncelikli destek'],
      recommended: true,
    },
    {
      key: 'enterprise',
      name: 'Kurumsal',
      price: 'Özel Fiyat',
      features: ['Sınırsız çalışan', 'Tam AI özellikleri', '7/24 destek'],
    },
  ];

  const handleCompanySubmit = async (values: CompanyFormData) => {
    setCompanyData(values);
    setCurrentStep(1);
  };

  const handleAdminSubmit = async (values: AdminFormData) => {
    setAdminData(values);
    setCurrentStep(2);
  };

  const handleFinalSubmit = async (values: PlanFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Simulating API call
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const registrationData = {
        company: companyData,
        admin: adminData,
        plan: values.plan,
        newsletter: values.newsletter,
      };

      console.log('Registration data:', registrationData);

      // TODO: Send to backend
      // const response = await fetch('/api/register', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(registrationData),
      // });

      message.success('Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz...');
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (err) {
      setError('Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  const steps = [
    {
      title: 'Şirket Bilgileri',
      icon: <BankOutlined />,
    },
    {
      title: 'Yönetici Hesabı',
      icon: <UserOutlined />,
    },
    {
      title: 'Plan Seçimi',
      icon: <CheckCircleOutlined />,
    },
  ];

  const renderCompanyForm = () => (
    <Form
      form={companyForm}
      layout="vertical"
      onFinish={handleCompanySubmit}
      size="large"
      requiredMark={false}
      initialValues={companyData || {}}
    >
      <Row gutter={16}>
        <Col span={24}>
          <Form.Item
            name="companyName"
            label="Şirket Adı"
            rules={[{ required: true, message: 'Şirket adı gereklidir' }]}
          >
            <Input prefix={<BankOutlined />} placeholder="Şirketinizin resmi adı" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="industry"
            label="Sektör"
            rules={[{ required: true, message: 'Sektör seçimi gereklidir' }]}
          >
            <Select placeholder="Sektör seçin">
              {industries.map((industry) => (
                <Option key={industry} value={industry}>
                  {industry}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="employeeCount"
            label="Çalışan Sayısı"
            rules={[{ required: true, message: 'Çalışan sayısı gereklidir' }]}
          >
            <Select placeholder="Çalışan sayısı seçin">
              {employeeCounts.map((count) => (
                <Option key={count} value={count}>
                  {count}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="country"
            label="Ülke"
            rules={[{ required: true, message: 'Ülke gereklidir' }]}
            initialValue="Türkiye"
          >
            <Select placeholder="Ülke seçin">
              <Option value="Türkiye">Türkiye</Option>
              <Option value="Almanya">Almanya</Option>
              <Option value="İngiltere">İngiltere</Option>
              <Option value="ABD">ABD</Option>
              <Option value="Diğer">Diğer</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="city"
            label="Şehir"
            rules={[{ required: true, message: 'Şehir gereklidir' }]}
          >
            <Input placeholder="Şehir" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        name="address"
        label="Adres"
        rules={[{ required: true, message: 'Adres gereklidir' }]}
      >
        <Input.TextArea rows={2} placeholder="Şirket adresi" />
      </Form.Item>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="phone"
            label="Telefon"
            rules={[{ required: true, message: 'Telefon gereklidir' }]}
          >
            <Input prefix={<PhoneOutlined />} placeholder="+90 XXX XXX XX XX" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="website" label="Web Sitesi (Opsiyonel)">
            <Input prefix={<GlobalOutlined />} placeholder="www.sirketiniz.com" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
        <Button type="primary" htmlType="submit" block style={{ height: 48 }}>
          Devam Et <ArrowRightOutlined />
        </Button>
      </Form.Item>
    </Form>
  );

  const renderAdminForm = () => (
    <Form
      form={adminForm}
      layout="vertical"
      onFinish={handleAdminSubmit}
      size="large"
      requiredMark={false}
      initialValues={adminData || {}}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="firstName"
            label="Ad"
            rules={[{ required: true, message: 'Ad gereklidir' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Adınız" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="lastName"
            label="Soyad"
            rules={[{ required: true, message: 'Soyad gereklidir' }]}
          >
            <Input placeholder="Soyadınız" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        name="jobTitle"
        label="Pozisyon"
        rules={[{ required: true, message: 'Pozisyon gereklidir' }]}
      >
        <Input prefix={<TeamOutlined />} placeholder="Örn: İK Müdürü, Operasyon Direktörü" />
      </Form.Item>

      <Form.Item
        name="email"
        label="İş E-posta Adresi"
        rules={[
          { required: true, message: 'E-posta gereklidir' },
          { type: 'email', message: 'Geçerli bir e-posta adresi girin' },
        ]}
      >
        <Input prefix={<MailOutlined />} placeholder="ad.soyad@sirket.com" />
      </Form.Item>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="password"
            label="Şifre"
            rules={[
              { required: true, message: 'Şifre gereklidir' },
              { min: 8, message: 'Şifre en az 8 karakter olmalıdır' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="En az 8 karakter" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="confirmPassword"
            label="Şifre Tekrar"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Şifre tekrarı gereklidir' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Şifreler eşleşmiyor'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Şifrenizi tekrar girin" />
          </Form.Item>
        </Col>
      </Row>

      <Space style={{ width: '100%', marginTop: 24 }}>
        <Button
          onClick={() => setCurrentStep(0)}
          style={{ height: 48, width: 120 }}
        >
          <ArrowLeftOutlined /> Geri
        </Button>
        <Button type="primary" htmlType="submit" style={{ height: 48, flex: 1 }}>
          Devam Et <ArrowRightOutlined />
        </Button>
      </Space>
    </Form>
  );

  const renderPlanForm = () => (
    <Form
      form={planForm}
      layout="vertical"
      onFinish={handleFinalSubmit}
      size="large"
      requiredMark={false}
      initialValues={{ plan: 'professional', newsletter: true }}
    >
      <Form.Item
        name="plan"
        rules={[{ required: true, message: 'Plan seçimi gereklidir' }]}
      >
        <Row gutter={16}>
          {plans.map((plan) => (
            <Col span={8} key={plan.key}>
              <Card
                hoverable
                style={{
                  borderColor: planForm.getFieldValue('plan') === plan.key ? '#1e3a5f' : '#e2e8f0',
                  borderWidth: plan.recommended ? 2 : 1,
                  position: 'relative',
                }}
                bodyStyle={{ padding: 16, textAlign: 'center' }}
                onClick={() => planForm.setFieldsValue({ plan: plan.key })}
              >
                {plan.recommended && (
                  <div
                    style={{
                      position: 'absolute',
                      top: -10,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: '#1e3a5f',
                      color: '#fff',
                      padding: '2px 12px',
                      borderRadius: 12,
                      fontSize: 11,
                    }}
                  >
                    Önerilen
                  </div>
                )}
                <Title level={5} style={{ marginBottom: 4 }}>
                  {plan.name}
                </Title>
                <Text strong style={{ color: '#1e3a5f', fontSize: 16 }}>
                  {plan.price}
                </Text>
                <Divider style={{ margin: '12px 0' }} />
                {plan.features.map((feature, i) => (
                  <div key={i} style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                    <CheckCircleOutlined style={{ color: '#22c55e', marginRight: 4 }} />
                    {feature}
                  </div>
                ))}
              </Card>
            </Col>
          ))}
        </Row>
      </Form.Item>

      <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, marginBottom: 24 }}>
        <Text style={{ fontSize: 13, color: '#64748b' }}>
          🎁 <strong>14 günlük ücretsiz deneme</strong> - Tüm planlarda geçerli. Kredi kartı gerektirmez.
        </Text>
      </div>

      <Form.Item
        name="agreeTerms"
        valuePropName="checked"
        rules={[
          {
            validator: (_, value) =>
              value ? Promise.resolve() : Promise.reject(new Error('Kullanım koşullarını kabul etmelisiniz')),
          },
        ]}
      >
        <Checkbox>
          <Text style={{ fontSize: 13 }}>
            <a href="#" style={{ color: '#1e3a5f' }}>Kullanım Koşulları</a>'nı okudum ve kabul ediyorum.
          </Text>
        </Checkbox>
      </Form.Item>

      <Form.Item
        name="agreePrivacy"
        valuePropName="checked"
        rules={[
          {
            validator: (_, value) =>
              value ? Promise.resolve() : Promise.reject(new Error('Gizlilik politikasını kabul etmelisiniz')),
          },
        ]}
      >
        <Checkbox>
          <Text style={{ fontSize: 13 }}>
            <a href="#" style={{ color: '#1e3a5f' }}>Gizlilik Politikası</a> ve <a href="#" style={{ color: '#1e3a5f' }}>KVKK Aydınlatma Metni</a>'ni okudum ve kabul ediyorum.
          </Text>
        </Checkbox>
      </Form.Item>

      <Form.Item name="newsletter" valuePropName="checked">
        <Checkbox>
          <Text style={{ fontSize: 13 }}>
            Ürün güncellemeleri ve kampanyalardan haberdar olmak istiyorum.
          </Text>
        </Checkbox>
      </Form.Item>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      <Space style={{ width: '100%', marginTop: 16 }}>
        <Button
          onClick={() => setCurrentStep(1)}
          style={{ height: 48, width: 120 }}
        >
          <ArrowLeftOutlined /> Geri
        </Button>
        <Button
          type="primary"
          htmlType="submit"
          loading={isLoading}
          style={{ height: 48, flex: 1 }}
        >
          <SafetyCertificateOutlined /> Kaydı Tamamla
        </Button>
      </Space>
    </Form>
  );

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        padding: '40px 24px',
      }}
    >
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Space
            style={{ cursor: 'pointer' }}
            onClick={() => router.push('/landing')}
          >
            <RobotOutlined style={{ fontSize: 36, color: '#1e3a5f' }} />
            <Title level={3} style={{ margin: 0, color: '#1e3a5f' }}>
              ShiftMaster AI
            </Title>
          </Space>
          <Paragraph style={{ color: '#64748b', marginTop: 8 }}>
            Şirketinizi kayıt edin ve yapay zeka destekli vardiya planlamaya başlayın
          </Paragraph>
        </div>

        {/* Steps */}
        <Card
          style={{
            borderRadius: 16,
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06)',
            marginBottom: 24,
          }}
          bodyStyle={{ padding: 24 }}
        >
          <Steps
            current={currentStep}
            items={steps}
            style={{ marginBottom: 8 }}
          />
        </Card>

        {/* Form Card */}
        <Card
          style={{
            borderRadius: 16,
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06)',
          }}
          bodyStyle={{ padding: 32 }}
        >
          <div style={{ marginBottom: 24 }}>
            <Title level={4} style={{ marginBottom: 4 }}>
              {steps[currentStep].title}
            </Title>
            <Text type="secondary">
              {currentStep === 0 && 'Şirketiniz hakkında temel bilgileri girin.'}
              {currentStep === 1 && 'Yönetici hesabınızı oluşturun.'}
              {currentStep === 2 && 'Size uygun planı seçin ve kayıt işlemini tamamlayın.'}
            </Text>
          </div>

          {currentStep === 0 && renderCompanyForm()}
          {currentStep === 1 && renderAdminForm()}
          {currentStep === 2 && renderPlanForm()}
        </Card>

        {/* Login Link */}
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text type="secondary">
            Zaten hesabınız var mı?{' '}
            <a
              onClick={() => router.push('/login')}
              style={{ color: '#1e3a5f', fontWeight: 500, cursor: 'pointer' }}
            >
              Giriş Yapın
            </a>
          </Text>
        </div>

        {/* Features */}
        <Row gutter={24} style={{ marginTop: 48 }}>
          {[
            { icon: <SafetyCertificateOutlined />, text: 'KVKK & GDPR Uyumlu' },
            { icon: <LockOutlined />, text: 'Kurumsal Güvenlik' },
            { icon: <TeamOutlined />, text: 'Sınırsız Destek' },
          ].map((item, i) => (
            <Col span={8} key={i}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#1e3a5f', fontSize: 24, marginBottom: 8 }}>{item.icon}</div>
                <Text style={{ fontSize: 13, color: '#64748b' }}>{item.text}</Text>
              </div>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
}
