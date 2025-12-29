import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { CheckCircle2, BookOpen, TrendingUp, Lightbulb, ArrowRight, Play, Target, Award, Clock } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface HomepageProps {
  onStartPractice: () => void;
}

export function Homepage({ onStartPractice }: HomepageProps) {
  const scrollToHowItWorks = () => {
    const element = document.getElementById('how-it-works');
    element?.scrollIntoView({ behavior: 'smooth' });
  };

  const features = [
    {
      icon: Target,
      title: "Step-by-Step Learning",
      description: "Break down complex problems into manageable steps. Each step is validated before you move forward."
    },
    {
      icon: BookOpen,
      title: "Real-Time Explanations",
      description: "Access detailed explanations alongside your work. No need to switch between tabs or pages."
    },
    {
      icon: TrendingUp,
      title: "Track Your Progress",
      description: "See your improvement over time with instant feedback and completion tracking."
    },
    {
      icon: Lightbulb,
      title: "Smart Hints",
      description: "Get helpful hints when you're stuck, without giving away the answer."
    }
  ];

  const subjects = [
    {
      name: "Mathematics",
      topics: ["Algebra", "Geometry", "Fractions", "Percentages", "Equations"],
      problems: 150,
      color: "bg-blue-500"
    },
    {
      name: "Science",
      topics: ["Physics", "Chemistry", "Biology", "Forces", "Cells"],
      problems: 120,
      color: "bg-green-500"
    },
    {
      name: "English",
      topics: ["Literature", "Writing", "Grammar", "Comprehension"],
      problems: 95,
      color: "bg-purple-500"
    }
  ];

  const stats = [
    { label: "Practice Problems", value: "365+" },
    { label: "Topics Covered", value: "50+" },
    { label: "Step-by-Step Solutions", value: "100%" },
    { label: "Success Rate", value: "94%" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-6 pt-16 pb-24">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <Badge className="mb-4 bg-blue-100 text-blue-700 hover:bg-blue-100">
              Interactive GCSE Learning Platform
            </Badge>
            <h1 className="text-5xl mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Master Your GCSEs with Step-by-Step Practice
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Learn at your own pace with interactive problems that guide you through every step. 
              Get instant feedback, detailed explanations, and track your progress in real-time.
            </p>
            <div className="flex gap-4 mb-8">
              <Button onClick={onStartPractice} size="lg" className="gap-2 text-lg px-8">
                Start Practicing Now
                <ArrowRight className="h-5 w-5" />
              </Button>
              <Button variant="outline" size="lg" className="gap-2 text-lg px-8" onClick={scrollToHowItWorks}>
                <Play className="h-5 w-5" />
                Watch Demo
              </Button>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span>Free practice problems</span>
              </div>
            </div>
          </div>
          <div className="relative">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border-8 border-white">
              <ImageWithFallback
                src="https://images.unsplash.com/photo-1614492898637-435e0f87cef8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdHVkZW50JTIwc3R1ZHlpbmclMjBtYXRoJTIwY29uZmlkZW50fGVufDF8fHx8MTc2MTIxMDMyOHww&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Student learning"
                className="w-full h-auto"
              />
            </div>
            {/* Floating stat card */}
            <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-lg p-4 border">
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-3 rounded-lg">
                  <Award className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl">94%</div>
                  <div className="text-sm text-gray-600">Success Rate</div>
                </div>
              </div>
            </div>
            {/* Floating progress card */}
            <div className="absolute -top-6 -right-6 bg-white rounded-xl shadow-lg p-4 border">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl">365+</div>
                  <div className="text-sm text-gray-600">Problems</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-white border-y py-12">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl mb-2 text-blue-600">{stat.value}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-4xl mb-4">Why Choose Our Platform?</h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            We've built the ultimate learning experience to help you ace your GCSEs with confidence
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
              <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-600">{feature.description}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Subjects Section */}
      <div className="bg-gray-50 py-20">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-4xl mb-4">Explore Subjects</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive coverage across all major GCSE subjects with hundreds of practice problems
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {subjects.map((subject, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-all hover:-translate-y-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`${subject.color} w-3 h-3 rounded-full`}></div>
                  <h3>{subject.name}</h3>
                </div>
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <Clock className="h-4 w-4" />
                    <span>{subject.problems} practice problems</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {subject.topics.slice(0, 4).map((topic, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                  {subject.topics.length > 4 && (
                    <Badge variant="outline" className="text-xs">
                      +{subject.topics.length - 4} more
                    </Badge>
                  )}
                </div>
                <Button 
                  variant="outline" 
                  className="w-full gap-2"
                  onClick={index === 0 ? onStartPractice : undefined}
                >
                  {index === 0 ? "Start Practicing" : "Coming Soon"}
                  {index === 0 && <ArrowRight className="h-4 w-4" />}
                </Button>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* How it Works */}
      <div id="how-it-works" className="container mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-4xl mb-4">How It Works</h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Get started in three simple steps
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-12 max-w-5xl mx-auto">
          <div className="text-center">
            <div className="bg-blue-500 text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">
              1
            </div>
            <h3 className="mb-3">Choose a Problem</h3>
            <p className="text-gray-600">
              Select from hundreds of GCSE-level problems across multiple subjects and difficulty levels
            </p>
          </div>
          <div className="text-center">
            <div className="bg-blue-500 text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">
              2
            </div>
            <h3 className="mb-3">Work Step-by-Step</h3>
            <p className="text-gray-600">
              Follow guided steps with instant validation and helpful hints when you need them
            </p>
          </div>
          <div className="text-center">
            <div className="bg-blue-500 text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">
              3
            </div>
            <h3 className="mb-3">Master the Concept</h3>
            <p className="text-gray-600">
              Review detailed explanations and track your progress as you build confidence
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl mb-4 text-white">Ready to Ace Your GCSEs?</h2>
          <p className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Join thousands of students who are improving their grades with our interactive learning platform
          </p>
          <Button 
            size="lg" 
            onClick={onStartPractice}
            className="bg-white text-blue-600 hover:bg-gray-100 gap-2 text-lg px-8"
          >
            Start Your First Problem
            <ArrowRight className="h-5 w-5" />
          </Button>
          <p className="text-sm text-blue-100 mt-4">
            No signup required • Free to use • Start immediately
          </p>
        </div>
      </div>
    </div>
  );
}
