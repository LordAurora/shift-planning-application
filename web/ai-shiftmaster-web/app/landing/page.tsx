'use client';

import React from 'react';
import {
  Layout,
  Typography,
  Button,
  Row,
  Col,
  Card,
  Space,
  Divider,
  Avatar,
  List,
} from 'antd';
import {
  RobotOutlined,
  CalendarOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
  LineChartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  CustomerServiceOutlined,
  RightOutlined,
  PlayCircleOutlined,
  StarFilled,
  BankOutlined,
  MobileOutlined,
  CloudOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';

const { Header, Content, Footer } = Layout;
const { Title, Text, Paragraph } = Typography;

export default function LandingPage() {
  const router = useRouter();

  const features = [
    {
      icon: <RobotOutlined style={{ fontSize: 40, color: '#1e3a5f' }} />,
      title: 'Yapay Zeka Destekli Optimizasyon',
      description: 'Gelişmiş AI algoritmaları ile vardiya planlamanızı otomatik olarak optimize edin. Çalışan tercihlerini, iş yükünü ve yasal gereksinimleri dengeleyin.',
    },
    {
      icon: <CalendarOutlined style={{ fontSize: 40, color: '#1e3a5f' }} />,
      title: 'Akıllı Vardiya Planlama',
      description: 'Sürükle-bırak arayüzü ile kolay vardiya oluşturma. Çakışmaları otomatik algılama ve çözümleme.',
    },
    {
      icon: <TeamOutlined style={{ fontSize: 40, color: '#1e3a5f' }} />,
      title: 'Çalışan Yönetimi',
      description: 'Tüm çalışan bilgilerini tek bir platformda yönetin. Yetenekler, sertifikalar ve tercihler.',
    },
    {
      icon: <SafetyCertificateOutlined style={{ fontSize: 40, color: '#1e3a5f' }} />,
      title: 'Uyumluluk ve Güvenlik',
      description: 'İş kanunları ve şirket politikalarına tam uyum. KVKK ve GDPR uyumlu veri güvenliği.',
    },
    {
      icon: <LineChartOutlined style={{ fontSize: 40, color: '#1e3a5f' }} />,
      title: 'Detaylı Raporlama',
      description: 'Gerçek zamanlı analitikler ve özelleştirilebilir raporlar. Verimlilik metriklerini takip edin.',
    },
    {
      icon: <ClockCircleOutlined style={{ fontSize: 40, color: '#1e3a5f' }} />,
      title: 'Zaman Tasarrufu',
      description: 'Manuel planlama süresini %80 oranında azaltın. Otomatik bildirimler ve hatırlatmalar.',
    },
  ];

  const benefits = [
    'Vardiya çakışmalarını %95 oranında azaltın',
    'Çalışan memnuniyetini %40 artırın',
    'Planlama süresini %80 kısaltın',
    'İşgücü maliyetlerini %25 optimize edin',
    'Yasal uyumluluk risklerini minimize edin',
    'Gerçek zamanlı görünürlük sağlayın',
  ];

  const testimonials = [
    {
      name: 'Ahmet Yılmaz',
      role: 'İK Direktörü',
      company: 'ABC Holding',
      content: 'ShiftMaster AI sayesinde 500 çalışanımızın vardiya planlamasını artık saatler yerine dakikalar içinde yapıyoruz.',
      avatar: 'A',
    },
    {
      name: 'Zeynep Kaya',
      role: 'Operasyon Müdürü',
      company: 'XYZ Lojistik',
      content: 'Yapay zeka önerileri sayesinde çalışan memnuniyetimiz önemli ölçüde arttı. Kesinlikle tavsiye ediyorum.',
      avatar: 'Z',
    },
    {
      name: 'Mehmet Demir',
      role: 'Genel Müdür',
      company: 'Tech Solutions',
      content: 'Modern arayüzü ve güçlü özellikleri ile vardiya yönetiminde devrim yarattı. ROI ilk ayda kendini amorti etti.',
      avatar: 'M',
    },
  ];

  const pricingPlans = [
    {
      name: 'Başlangıç',
      price: '₺999',
      period: '/ay',
      description: 'Küçük ekipler için ideal',
      features: [
        '25 çalışana kadar',
        'Temel vardiya planlama',
        'E-posta desteği',
        'Mobil uygulama erişimi',
        'Temel raporlama',
      ],
      highlighted: false,
    },
    {
      name: 'Profesyonel',
      price: '₺2,499',
      period: '/ay',
      description: 'Büyüyen şirketler için',
      features: [
        '100 çalışana kadar',
        'AI destekli optimizasyon',
        'Öncelikli destek',
        'Gelişmiş raporlama',
        'API erişimi',
        'Özel entegrasyonlar',
      ],
      highlighted: true,
    },
    {
      name: 'Kurumsal',
      price: 'Özel Fiyat',
      period: '',
      description: 'Büyük işletmeler için',
      features: [
        'Sınırsız çalışan',
        'Tam AI özellikleri',
        '7/24 destek',
        'Özel eğitim',
        'SLA garantisi',
        'On-premise seçeneği',
      ],
      highlighted: false,
    },
  ];

  const stats = [
    { value: '500+', label: 'Aktif Şirket' },
    { value: '50,000+', label: 'Yönetilen Çalışan' },
    { value: '%99.9', label: 'Uptime' },
    { value: '4.9/5', label: 'Müşteri Puanı' },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#fff' }}>
      {/* Header */}
      <Header
        style={{
          position: 'fixed',
          zIndex: 1000,
          width: '100%',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid #f0f0f0',
          padding: '0 50px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: 70,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <RobotOutlined style={{ fontSize: 32, color: '#1e3a5f' }} />
          <Title level={4} style={{ margin: 0, color: '#1e3a5f' }}>
            ShiftMaster AI
          </Title>
        </div>
        <Space size="middle">
          <Button type="link" style={{ color: '#1e3a5f' }} onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>
            Özellikler
          </Button>
          <Button type="link" style={{ color: '#1e3a5f' }} onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}>
            Fiyatlandırma
          </Button>
          <Button type="link" style={{ color: '#1e3a5f' }} onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}>
            İletişim
          </Button>
          <Button onClick={() => router.push('/login')}>Giriş Yap</Button>
          <Button type="primary" onClick={() => router.push('/register')}>
            Ücretsiz Başla
          </Button>
        </Space>
      </Header>

      <Content>
        {/* Hero Section */}
        <div
          style={{
            background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #4a7c9b 100%)',
            padding: '140px 50px 100px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.03"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
            }}
          />
          <Row gutter={[48, 48]} align="middle" style={{ maxWidth: 1400, margin: '0 auto', position: 'relative' }}>
            <Col xs={24} lg={12}>
              <Space direction="vertical" size={24}>
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    padding: '6px 16px',
                    borderRadius: 20,
                    display: 'inline-block',
                  }}
                >
                  <Text style={{ color: '#fff', fontSize: 14 }}>
                    🚀 Türkiye'nin #1 Vardiya Planlama Platformu
                  </Text>
                </div>
                <Title style={{ color: '#fff', fontSize: 48, margin: 0, lineHeight: 1.2 }}>
                  Yapay Zeka ile
                  <br />
                  <span style={{ color: '#7dd3fc' }}>Akıllı Vardiya</span>
                  <br />
                  Planlama
                </Title>
                <Paragraph style={{ color: 'rgba(255, 255, 255, 0.85)', fontSize: 18, maxWidth: 500 }}>
                  ShiftMaster AI, çalışan vardiyalarını optimize eden, iş gücü verimliliğini artıran 
                  ve operasyonel maliyetleri düşüren yapay zeka destekli kurumsal çözümdür.
                </Paragraph>
                <Space size="middle">
                  <Button
                    type="primary"
                    size="large"
                    icon={<RightOutlined />}
                    onClick={() => router.push('/register')}
                    style={{
                      height: 50,
                      paddingLeft: 32,
                      paddingRight: 32,
                      fontSize: 16,
                      background: '#fff',
                      color: '#1e3a5f',
                      border: 'none',
                    }}
                  >
                    14 Gün Ücretsiz Deneyin
                  </Button>
                  <Button
                    size="large"
                    icon={<PlayCircleOutlined />}
                    style={{
                      height: 50,
                      paddingLeft: 32,
                      paddingRight: 32,
                      fontSize: 16,
                      background: 'transparent',
                      color: '#fff',
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    }}
                  >
                    Demo İzle
                  </Button>
                </Space>
                <div style={{ marginTop: 16 }}>
                  <Text style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: 13 }}>
                    ✓ Kredi kartı gerektirmez &nbsp;&nbsp; ✓ Kurulum desteği dahil &nbsp;&nbsp; ✓ İstediğiniz zaman iptal edin
                  </Text>
                </div>
              </Space>
            </Col>
            <Col xs={24} lg={12}>
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: 20,
                  padding: 24,
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                }}
              >
                <div
                  style={{
                    background: '#fff',
                    borderRadius: 12,
                    padding: 20,
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f57' }} />
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#febc2e' }} />
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#28c840' }} />
                  </div>
                  <div style={{ background: '#f8fafc', borderRadius: 8, padding: 16 }}>
                    <Row gutter={[8, 8]}>
                      {['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'].map((day) => (
                        <Col span={3} key={day}>
                          <div style={{ textAlign: 'center', fontSize: 11, color: '#64748b', fontWeight: 500 }}>
                            {day}
                          </div>
                        </Col>
                      ))}
                      {[...Array(7)].map((_, i) => (
                        <Col span={3} key={i}>
                          <div
                            style={{
                              background: i === 3 ? '#1e3a5f' : i < 5 ? '#e2e8f0' : '#f1f5f9',
                              height: 40,
                              borderRadius: 6,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            {i === 3 && <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />}
                          </div>
                        </Col>
                      ))}
                    </Row>
                    <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <ThunderboltOutlined style={{ color: '#1e3a5f' }} />
                      <Text style={{ fontSize: 12, color: '#64748b' }}>AI Optimizasyonu Aktif</Text>
                    </div>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </div>

        {/* Stats Section */}
        <div style={{ background: '#f8fafc', padding: '60px 50px' }}>
          <Row gutter={[48, 24]} justify="center" style={{ maxWidth: 1200, margin: '0 auto' }}>
            {stats.map((stat, index) => (
              <Col xs={12} sm={6} key={index}>
                <div style={{ textAlign: 'center' }}>
                  <Title level={2} style={{ color: '#1e3a5f', marginBottom: 4 }}>
                    {stat.value}
                  </Title>
                  <Text type="secondary">{stat.label}</Text>
                </div>
              </Col>
            ))}
          </Row>
        </div>

        {/* Features Section */}
        <div id="features" style={{ padding: '100px 50px', background: '#fff' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 60 }}>
              <Text
                style={{
                  color: '#1e3a5f',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                  fontSize: 13,
                }}
              >
                Özellikler
              </Text>
              <Title level={2} style={{ marginTop: 12, marginBottom: 16 }}>
                Neden ShiftMaster AI?
              </Title>
              <Paragraph style={{ color: '#64748b', fontSize: 16, maxWidth: 600, margin: '0 auto' }}>
                Modern iş gücü yönetimi için ihtiyacınız olan tüm araçlar tek bir platformda.
                Yapay zeka destekli çözümlerle verimliliğinizi artırın.
              </Paragraph>
            </div>

            <Row gutter={[32, 32]}>
              {features.map((feature, index) => (
                <Col xs={24} sm={12} lg={8} key={index}>
                  <Card
                    hoverable
                    style={{
                      height: '100%',
                      borderRadius: 16,
                      border: '1px solid #e2e8f0',
                      transition: 'all 0.3s ease',
                    }}
                    bodyStyle={{ padding: 32 }}
                  >
                    <div style={{ marginBottom: 20 }}>{feature.icon}</div>
                    <Title level={4} style={{ marginBottom: 12 }}>
                      {feature.title}
                    </Title>
                    <Paragraph style={{ color: '#64748b', marginBottom: 0 }}>
                      {feature.description}
                    </Paragraph>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </div>

        {/* Benefits Section */}
        <div style={{ background: '#1e3a5f', padding: '100px 50px' }}>
          <Row gutter={[64, 48]} align="middle" style={{ maxWidth: 1200, margin: '0 auto' }}>
            <Col xs={24} lg={12}>
              <Text
                style={{
                  color: '#7dd3fc',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                  fontSize: 13,
                }}
              >
                Avantajlar
              </Text>
              <Title level={2} style={{ color: '#fff', marginTop: 12, marginBottom: 24 }}>
                İşletmenizi Dönüştürün
              </Title>
              <Paragraph style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: 16, marginBottom: 32 }}>
                ShiftMaster AI ile operasyonel verimliliğinizi artırın, 
                maliyetlerinizi düşürün ve çalışan memnuniyetini yükseltin.
              </Paragraph>
              <List
                dataSource={benefits}
                renderItem={(item) => (
                  <List.Item style={{ border: 'none', padding: '8px 0' }}>
                    <Space>
                      <CheckCircleOutlined style={{ color: '#7dd3fc', fontSize: 20 }} />
                      <Text style={{ color: '#fff', fontSize: 16 }}>{item}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Col>
            <Col xs={24} lg={12}>
              <Row gutter={[16, 16]}>
                {[
                  { icon: <MobileOutlined />, title: 'Mobil Uygulama', desc: 'iOS ve Android desteği' },
                  { icon: <CloudOutlined />, title: 'Bulut Tabanlı', desc: 'Her yerden erişim' },
                  { icon: <LockOutlined />, title: 'Güvenli', desc: 'Kurumsal güvenlik' },
                  { icon: <GlobalOutlined />, title: 'Çok Dilli', desc: 'Türkçe ve İngilizce' },
                ].map((item, index) => (
                  <Col span={12} key={index}>
                    <Card
                      style={{
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 12,
                      }}
                      bodyStyle={{ padding: 24 }}
                    >
                      <div style={{ color: '#7dd3fc', fontSize: 32, marginBottom: 12 }}>{item.icon}</div>
                      <Title level={5} style={{ color: '#fff', marginBottom: 4 }}>
                        {item.title}
                      </Title>
                      <Text style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{item.desc}</Text>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Col>
          </Row>
        </div>

        {/* Testimonials Section */}
        <div style={{ background: '#f8fafc', padding: '100px 50px' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 60 }}>
              <Text
                style={{
                  color: '#1e3a5f',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                  fontSize: 13,
                }}
              >
                Referanslar
              </Text>
              <Title level={2} style={{ marginTop: 12, marginBottom: 16 }}>
                Müşterilerimiz Ne Diyor?
              </Title>
            </div>

            <Row gutter={[32, 32]}>
              {testimonials.map((testimonial, index) => (
                <Col xs={24} md={8} key={index}>
                  <Card
                    style={{
                      height: '100%',
                      borderRadius: 16,
                      border: 'none',
                      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06)',
                    }}
                    bodyStyle={{ padding: 32 }}
                  >
                    <div style={{ marginBottom: 16 }}>
                      {[...Array(5)].map((_, i) => (
                        <StarFilled key={i} style={{ color: '#fbbf24', marginRight: 4 }} />
                      ))}
                    </div>
                    <Paragraph style={{ color: '#475569', fontSize: 15, lineHeight: 1.7 }}>
                      "{testimonial.content}"
                    </Paragraph>
                    <Divider style={{ margin: '20px 0' }} />
                    <Space>
                      <Avatar style={{ background: '#1e3a5f' }}>{testimonial.avatar}</Avatar>
                      <div>
                        <Text strong>{testimonial.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 13 }}>
                          {testimonial.role}, {testimonial.company}
                        </Text>
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </div>

        {/* Pricing Section */}
        <div id="pricing" style={{ padding: '100px 50px', background: '#fff' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: 60 }}>
              <Text
                style={{
                  color: '#1e3a5f',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                  fontSize: 13,
                }}
              >
                Fiyatlandırma
              </Text>
              <Title level={2} style={{ marginTop: 12, marginBottom: 16 }}>
                Şirketinize Uygun Plan Seçin
              </Title>
              <Paragraph style={{ color: '#64748b', fontSize: 16, maxWidth: 600, margin: '0 auto' }}>
                Tüm planlar 14 günlük ücretsiz deneme süresi içerir. İstediğiniz zaman iptal edebilirsiniz.
              </Paragraph>
            </div>

            <Row gutter={[32, 32]} justify="center">
              {pricingPlans.map((plan, index) => (
                <Col xs={24} md={8} key={index}>
                  <Card
                    style={{
                      height: '100%',
                      borderRadius: 16,
                      border: plan.highlighted ? '2px solid #1e3a5f' : '1px solid #e2e8f0',
                      position: 'relative',
                      overflow: 'visible',
                    }}
                    bodyStyle={{ padding: 32 }}
                  >
                    {plan.highlighted && (
                      <div
                        style={{
                          position: 'absolute',
                          top: -12,
                          left: '50%',
                          transform: 'translateX(-50%)',
                          background: '#1e3a5f',
                          color: '#fff',
                          padding: '4px 16px',
                          borderRadius: 20,
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        En Popüler
                      </div>
                    )}
                    <Title level={4} style={{ marginBottom: 8 }}>
                      {plan.name}
                    </Title>
                    <Text type="secondary">{plan.description}</Text>
                    <div style={{ margin: '24px 0' }}>
                      <Title level={2} style={{ marginBottom: 0, display: 'inline' }}>
                        {plan.price}
                      </Title>
                      <Text type="secondary">{plan.period}</Text>
                    </div>
                    <List
                      dataSource={plan.features}
                      renderItem={(item) => (
                        <List.Item style={{ border: 'none', padding: '8px 0' }}>
                          <Space>
                            <CheckCircleOutlined style={{ color: '#22c55e' }} />
                            <Text>{item}</Text>
                          </Space>
                        </List.Item>
                      )}
                    />
                    <Button
                      type={plan.highlighted ? 'primary' : 'default'}
                      size="large"
                      block
                      style={{ marginTop: 24, height: 48 }}
                      onClick={() => router.push('/register')}
                    >
                      {plan.price === 'Özel Fiyat' ? 'İletişime Geç' : 'Hemen Başla'}
                    </Button>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </div>

        {/* CTA Section */}
        <div
          style={{
            background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)',
            padding: '80px 50px',
            textAlign: 'center',
          }}
        >
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Title level={2} style={{ color: '#fff', marginBottom: 16 }}>
              Vardiya Planlamada Yeni Nesil Deneyim
            </Title>
            <Paragraph style={{ color: 'rgba(255, 255, 255, 0.85)', fontSize: 18, marginBottom: 32 }}>
              Şirketinizi ShiftMaster AI ile tanıştırın. 14 gün ücretsiz deneyin, 
              farkı hemen görün.
            </Paragraph>
            <Space size="middle">
              <Button
                type="primary"
                size="large"
                onClick={() => router.push('/register')}
                style={{
                  height: 50,
                  paddingLeft: 40,
                  paddingRight: 40,
                  fontSize: 16,
                  background: '#fff',
                  color: '#1e3a5f',
                  border: 'none',
                }}
              >
                Ücretsiz Kayıt Ol
              </Button>
              <Button
                size="large"
                icon={<CustomerServiceOutlined />}
                style={{
                  height: 50,
                  paddingLeft: 32,
                  paddingRight: 32,
                  fontSize: 16,
                  background: 'transparent',
                  color: '#fff',
                  borderColor: 'rgba(255, 255, 255, 0.5)',
                }}
              >
                Demo Talep Et
              </Button>
            </Space>
          </div>
        </div>

        {/* Contact Section */}
        <div id="contact" style={{ padding: '80px 50px', background: '#f8fafc' }}>
          <Row gutter={[64, 48]} style={{ maxWidth: 1200, margin: '0 auto' }}>
            <Col xs={24} md={8}>
              <Title level={4}>ShiftMaster AI</Title>
              <Paragraph style={{ color: '#64748b' }}>
                Yapay zeka destekli vardiya planlama çözümü ile iş gücü yönetiminizi dönüştürün.
              </Paragraph>
              <Space>
                <BankOutlined style={{ fontSize: 20, color: '#1e3a5f' }} />
                <GlobalOutlined style={{ fontSize: 20, color: '#1e3a5f' }} />
                <CustomerServiceOutlined style={{ fontSize: 20, color: '#1e3a5f' }} />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Title level={5}>Ürün</Title>
              <Space direction="vertical" size={8}>
                <Text style={{ color: '#64748b', cursor: 'pointer' }}>Özellikler</Text>
                <Text style={{ color: '#64748b', cursor: 'pointer' }}>Fiyatlandırma</Text>
                <Text style={{ color: '#64748b', cursor: 'pointer' }}>Entegrasyonlar</Text>
                <Text style={{ color: '#64748b', cursor: 'pointer' }}>API Dokümantasyonu</Text>
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Title level={5}>İletişim</Title>
              <Space direction="vertical" size={8}>
                <Text style={{ color: '#64748b' }}>📧 info@shiftmaster.ai</Text>
                <Text style={{ color: '#64748b' }}>📞 +90 212 555 0000</Text>
                <Text style={{ color: '#64748b' }}>📍 İstanbul, Türkiye</Text>
              </Space>
            </Col>
          </Row>
        </div>
      </Content>

      {/* Footer */}
      <Footer
        style={{
          background: '#1e3a5f',
          padding: '24px 50px',
          textAlign: 'center',
        }}
      >
        <Text style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
          © 2024 ShiftMaster AI. Tüm hakları saklıdır. | Gizlilik Politikası | Kullanım Koşulları
        </Text>
      </Footer>
    </Layout>
  );
}
