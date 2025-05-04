"use client";
import GradientText from '@/ReactBits/GradientText/GradientText';

const Hero = () => {

  return (
    <section>
      <div className={`flex justify-center items-center h-[100px] w-full`} >
        <div className='flex justify-center items-center w-full'>
          <h1 className='sm:text-4xl text-xl font-bold text-white font-italic'>
          <GradientText
            colors={["#40ffaa", "#4079ff", "#40ffaa", "#4079ff", "#40ffaa"]}
            animationSpeed={3}
            showBorder={false}
            className="custom-class"
          >
            Tabularis - VLM For Better Understanding
          </GradientText>
        </h1>
        </div>
      </div>
    </section>
  );
};

export default Hero;